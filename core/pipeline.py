"""End-to-end run: question -> plan -> search -> read -> claims -> code checks -> brief."""
from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from typing import Callable

from . import extract
from .analyze import build_findings, context_flags, definition_differences, enrich_claim, norm_market
from .brief import write_brief
from .fetch import fetch
from .llm import LLM, LLMError
from .models import Claim, Source
from .periods import Window, question_window
from .search import search, search_engine_name
from .sources import assess_claim, assess_source, base_tier, domain_of
from .textnorm import normalize
from .verify import verify_claim

TIER_RANK = {"A": 0, "B": 1, "C": 2, "D": 3}


def _noop(msg: str) -> None:
    pass


def collect_urls(queries: list[str], extra_urls: list[str], per_query: int, progress) -> tuple[list[dict], list[dict]]:
    """Return (candidates, search_log). User-given URLs come first, then search results."""
    seen, cands, log = set(), [], []
    for u in extra_urls:
        u = u.strip()
        if u and u not in seen:
            seen.add(u)
            cands.append({"url": u, "title": "", "published": None, "from": "người dùng"})
    for q in queries:
        progress(f"Tìm kiếm ({search_engine_name()}): {q}")
        try:
            results = search(q, per_query)
        except Exception as e:
            log.append({"query": q, "error": str(e), "results": []})
            continue
        log.append({"query": q, "results": [r["url"] for r in results]})
        for r in results:
            if r["url"] and r["url"] not in seen:
                seen.add(r["url"])
                cands.append({**r, "from": q})
    return cands, log


def _window(w: dict) -> Window:
    return Window(date.fromisoformat(w["start"]), date.fromisoformat(w["end"]), w["kind"], w["label"])


def _carry(prior: dict, window: Window, q_market: str, today: date) -> tuple[list[Source], list[Claim]]:
    """Sources and claims of the previous run, with question-dependent flags redone for the new question.
    Claims keep their ids, verification and the user's exclusions."""
    old_w, old_today = _window(prior["window"]), date.fromisoformat(prior["today"])
    sources = [Source(**{**s, "text": ""}) for s in prior["sources"]]
    claims = [Claim(**c) for c in prior["claims"]]
    for c in claims:
        if c.verified:
            old = set(context_flags(c, old_w, prior["question_market"], old_today))
            c.flags = [f for f in c.flags if f not in old] + context_flags(c, window, q_market, today)
            c.flags = list(dict.fromkeys(c.flags))
    return sources, claims


def run(question: str, plan: dict | None = None, extra_urls: list[str] | None = None,
        uploads: list[Source] | None = None, use_search: bool = True, max_sources: int = 8,
        per_query: int = 5, llm: LLM | None = None, today: date | None = None,
        upload_tier: str = "B", progress: Callable[[str], None] = _noop, prior: dict | None = None,
        reread: bool = False) -> dict:
    """`prior` is a previous result: its verified claims are carried as context. Its pages are skipped in
    search results; with `reread` the pages that gave verified claims are read again (from the local copy)
    for the new question, since a new angle can need numbers the first reading did not pick up."""
    t0 = time.time()
    today = today or date.today()
    llm = llm or LLM()
    calls0 = llm.calls
    if plan is None:
        progress("Lập kế hoạch: tách tiêu chí và viết truy vấn")
        plan = extract.plan(llm, question, today)
    window = question_window(question, today)
    q_market = norm_market(plan.get("market", "")) if plan.get("market") else "chưa rõ"

    old_sources, old_claims = _carry(prior, window, q_market, today) if prior else ([], [])
    read_before = {s.url for s in old_sources}
    useful = {c.source_id for c in old_claims if c.verified}
    again = [s.url for s in old_sources if reread and s.id in useful and s.url.startswith("http")]
    cands, search_log = collect_urls(plan.get("queries", []) if use_search else [], again + list(extra_urls or []),
                                     per_query, progress)
    # better sources first: user links, then A, B, C; D pages are listed but never read
    skipped = []
    ranked = []
    for i, c in enumerate(cands):
        if c["url"] in read_before and c["from"] != "người dùng":
            skipped.append({"url": c["url"], "reason": "Đã đọc ở lần nghiên cứu trước, nhận định được giữ lại"})
            continue
        tier, _ = base_tier(domain_of(c["url"]))
        if tier == "D" and c["from"] != "người dùng":
            skipped.append({"url": c["url"], "reason": "Hạng D (trang SEO hoặc bán báo cáo): không dùng làm bằng chứng"})
            continue
        ranked.append((0 if c["from"] == "người dùng" else 1, TIER_RANK[tier], i, c))
    ranked.sort(key=lambda x: x[:3])
    chosen = [x[3] for x in ranked[:max_sources]]
    skipped += [{"url": x[3]["url"], "reason": "Vượt số nguồn tối đa mỗi lần chạy"} for x in ranked[max_sources:]]

    progress(f"Đọc {len(chosen)} nguồn")
    with ThreadPoolExecutor(max_workers=6) as ex:
        fetched = list(ex.map(lambda c: fetch(c["url"], c.get("published")), chosen))
    sources: list[Source] = fetched + list(uploads or [])
    for s in sources:
        assess_source(s, today, upload_tier)

    first = 1 + max((int(c.id[1:]) for c in old_claims if c.id[1:].isdigit()), default=0)
    claims: list[Claim] = []
    llm_error = ""          # set when the AI could not be called, so the run is not mistaken for a finding
    for s in sources:
        if s.error or not s.text:
            continue
        progress(f"Trích nhận định: {s.title[:60] or s.domain}")
        try:
            claims += extract.extract_claims(llm, question, plan["criteria"], s, start_index=first + len(claims))
        except Exception as e:
            s.error = f"Lỗi khi trích nhận định: {e}"
            llm_error = str(e) if isinstance(e, LLMError) else llm_error

    progress("Kiểm câu trích bằng code, chấm hạng nguồn, so sánh số liệu")
    by_id = {s.id: s for s in sources}
    for c in claims:
        s = by_id[c.source_id]
        verify_claim(c, s)
        if c.verified:
            assess_claim(c, s)
            enrich_claim(c, window, q_market, today, s.published)
    # a page read again replaces its old copy; claims from both stay, ids never clash, and a claim found
    # again (same page, quote and value) keeps its old id
    by_id = {**{s.id: s for s in old_sources}, **by_id}
    sources = list(by_id.values())
    seen = {(c.source_id, normalize(c.quote), normalize(c.value_text)) for c in old_claims}
    claims = old_claims + [c for c in claims if (c.source_id, normalize(c.quote), normalize(c.value_text)) not in seen]
    findings = build_findings(claims, by_id, today)
    claim_map = {c.id: c for c in claims}
    def_notes = definition_differences(findings, claim_map)

    progress("Viết bản tóm tắt từ các nhận định đã kiểm")
    try:
        brief = write_brief(llm, question, plan["criteria"], claims, findings, def_notes, window, by_id, q_market)
    except LLMError as e:
        llm_error = str(e)
        brief = write_brief(None, question, plan["criteria"], claims, findings, def_notes, window, by_id, q_market)
        if any(c.verified for c in claims):
            brief["summary"] = ("Không viết được bản tóm tắt vì lỗi gọi AI. Các nhận định đã kiểm chứng vẫn được "
                                "liệt kê ở tab Nhận định đã kiểm; có thể bấm viết lại bản tóm tắt sau.")
            brief["confidence"] = "Chưa đánh giá"
        brief["guard_log"].append(f"Lỗi khi viết bản tóm tắt: {e}")

    if not any(c.verified for c in claims) and sources and (all(s.error for s in sources) or any("Lỗi khi trích nhận định" in (s.error or "") for s in sources)):
        brief["summary"] = (f"Chưa trả lời được do lỗi kỹ thuật khi gọi AI, không phải do thiếu dữ liệu. {llm_error}" if llm_error else
                            "Chưa thể trả lời do gặp lỗi kỹ thuật khi đọc hoặc xử lý nguồn. "
                            "Vui lòng kiểm tra lại kết nối mạng hoặc thử lại sau.")
        brief["confidence"] = "Chưa đánh giá"

    rid = uuid.uuid4().hex[:10]
    thread = (prior.get("thread") or [{"id": prior["id"], "question": prior["question"]}]) if prior else []
    return {
        "id": rid,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "question": question,
        "parent_id": prior["id"] if prior else None,
        "thread": thread + [{"id": rid, "question": question}],
        "today": today.isoformat(),
        "plan": plan,
        "window": {"start": window.start.isoformat(), "end": window.end.isoformat(),
                   "kind": window.kind, "label": window.label},
        "question_market": q_market,
        "search_log": search_log,
        "skipped": skipped,
        "sources": [s.to_dict() for s in sources],
        "claims": [c.to_dict() for c in claims],
        "findings": [f.to_dict() for f in findings],
        "brief": brief,
        "stats": {
            "sources_read": sum(1 for s in sources if not s.error),
            "sources_failed": sum(1 for s in sources if s.error),
            "claims": len(claims),
            "verified": sum(1 for c in claims if c.verified),
            "rejected": sum(1 for c in claims if not c.verified),
            "carried": sum(1 for c in old_claims if c.verified),
            "llm_calls": llm.calls - calls0,
            "seconds": round(time.time() - t0, 1),
            "model": f"{llm.provider}/{', '.join(sorted(getattr(llm, 'models_used', set()) or {llm.model}))}",
            "search": search_engine_name() if use_search else "tắt",
            "llm_error": llm_error,
        },
    }


def rebrief(result: dict, excluded_ids: set[str], llm: LLM | None = None) -> dict:
    """Second human checkpoint: the user drops claims they judge wrong, the brief is rebuilt."""
    llm = llm or LLM()
    today = date.fromisoformat(result["today"])
    window = _window(result["window"])
    sources = {s["id"]: Source(**{**s, "text": ""}) for s in result["sources"]}
    claims = [Claim(**c) for c in result["claims"]]
    for c in claims:
        c.excluded_by_user = c.id in excluded_ids
    findings = build_findings(claims, sources, today)
    def_notes = definition_differences(findings, {c.id: c for c in claims})
    result = dict(result)
    result["claims"] = [c.to_dict() for c in claims]
    result["findings"] = [f.to_dict() for f in findings]
    result["brief"] = write_brief(llm, result["question"], result["plan"]["criteria"], claims, findings,
                                  def_notes, window, sources, result.get("question_market", ""))
    result["brief"]["guard_log"].append(f"Người dùng loại {len(excluded_ids)} nhận định: {', '.join(sorted(excluded_ids))}")
    return result


def follow_up(prev: dict, follow_question: str = "", queries: list[str] | None = None,
              extra_urls: list[str] | None = None, use_search: bool = True, max_sources: int = 6,
              llm: LLM | None = None, today: date | None = None, progress: Callable[[str], None] = _noop) -> dict:
    """Research further from a previous result without losing its context.

    A typed follow-up ("Còn Việt Nam thì sao?") is rewritten into a full question with the previous one as
    context. A next step from the brief comes with its own search query and keeps the previous question.
    Either way the verified claims, sources and user exclusions of `prev` are carried over.
    """
    llm = llm or LLM()
    calls0 = llm.calls
    if follow_question.strip():
        progress("Lập kế hoạch cho câu hỏi tiếp theo, giữ bối cảnh câu hỏi trước")
        plan = extract.plan_followup(llm, prev, follow_question.strip(), today)
        question = plan.pop("standalone_question")
    else:
        plan = {**prev["plan"], "queries": list(queries or [])}
        question = prev["question"]
    res = run(question, plan=plan, extra_urls=extra_urls, use_search=use_search, max_sources=max_sources,
              llm=llm, today=today, progress=progress, prior=prev, reread=bool(follow_question.strip()))
    res["asked"] = follow_question.strip() or "; ".join(queries or [])
    res["stats"]["llm_calls"] = llm.calls - calls0
    return res
