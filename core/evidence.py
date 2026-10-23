"""What can be trusted, what is still uncertain, and where to look next.

Sorting is done by fixed rules over the findings, so the same evidence always lands in the
same place and the LLM never decides what is trustworthy. Every uncertain item says why and
comes with a next step: a ready search query, a follow-up question, or a link to open.
"""
from __future__ import annotations

from collections import defaultdict
from urllib.parse import quote as urlquote

from .analyze import MARKET_ALIASES
from .models import Claim, Finding, Source
from .periods import Window, parse_period
from .sources import load_config
from .textnorm import fmt_value

UNCERTAIN_FLAGS = ("ngoài khung", "cần xem lại phạm vi", "dự báo", "không phải số của cả",
                   "Không xác định được kỳ đo", "Tăng trưởng trên 100%", "coi là USD", "không ghi rõ thị trường")
RELAYED = "chưa đối chiếu bản gốc"
ONLY_CD = "Chỉ có nguồn hạng C hoặc D"
CHART_MIN_NUMBERS = 3       # this many bare-number quotes on one page usually means a chart or table

MARKET_EN = {name: aliases[0].title() for name, aliases in MARKET_ALIASES.items()}
METRIC_EN = {"revenue": "revenue", "growth": "revenue growth", "downloads": "downloads", "players": "players",
             "share": "market share", "rank": "ranking", "other": ""}
SCOPE_EN = {"all_games": "games market", "mobile": "mobile games", "mobile_iap": "mobile games in-app purchase",
            "pc_console": "PC console games", "unknown": "games"}


def evidence_url(url: str, kind: str, quote: str, page: int | None) -> str:
    """Link that opens the source at the quote: a text fragment for web pages, the page for PDFs."""
    if kind == "upload" or not url.startswith("http"):
        return ""
    url = url.split("#")[0]
    if kind == "pdf":
        return f"{url}#page={page}" if page else url
    words = " ".join((quote or "").replace("|", " ").split()).split(" ")
    if not words[0]:
        return url

    def enc(s: str) -> str:
        return urlquote(s, safe="").replace("-", "%2D")     # '-' and ',' are syntax in text fragments

    frag = enc(" ".join(words)) if len(words) <= 10 else enc(" ".join(words[:5])) + "," + enc(" ".join(words[-5:]))
    return f"{url}#:~:text={frag}"


def claim_link(c: Claim, s: Source | None) -> str:
    return evidence_url(s.url, s.kind, c.quote, c.page) if s else ""


def _terms(c: Claim, market: str = "", period: str | None = None) -> str:
    m = market or c.market
    parts = [MARKET_EN.get(m, m), SCOPE_EN.get(c.scope, "games"), c.genre, METRIC_EN.get(c.metric, ""),
             c.period if period is None else period]
    return " ".join(p for p in parts if p).strip()


def _step(text: str, query: str = "", ask: str = "", url: str = "", finding: str = "") -> dict:
    return {"text": text, "query": query, "ask": ask, "url": url, "findings": [finding] if finding else []}


def _values(f: Finding) -> str:
    return " đến ".join(dict.fromkeys(fmt_value(v, f.unit) for v in sorted(f.values)))


def off_scope(f: Finding, rep: Claim, window: Window) -> str:
    """Why a finding does not answer the question as asked (another market or period), or '' if it does.
    Older data for a relative time frame ("12 tháng qua") is kept as uncertain evidence, not hidden."""
    geo = next((fl for fl in rep.flags if "câu hỏi hỏi về" in fl), "")
    if geo:
        return geo
    sp = parse_period(rep.period)
    if sp and sp.start > window.end and window.kind != "future":
        return f"Kỳ đo {rep.period} nằm sau khung thời gian câu hỏi ({window.label})"
    if sp and window.kind == "specific" and sp.end < window.start:
        return f"Kỳ đo {rep.period} nằm trước khung thời gian câu hỏi ({window.label})"
    if f.newer and window.kind != "specific":
        return f"Đã có số mới hơn cho cùng chỉ số ({f.newer})"
    return ""


def judge(f: Finding, claims: dict[str, Claim], sources: dict[str, Source], window: Window,
          question_market: str) -> tuple[list[str], list[dict], list[str]]:
    """Return (why this finding is uncertain, next steps, notes). No reasons means it can be trusted;
    notes are caveats that do not stop trust, such as a reputable article quoting the data firm."""
    cs = [claims[i] for i in f.claim_ids]
    rep = cs[0]
    why, steps, notes = [], [], []
    link = claim_link(rep, sources.get(rep.source_id))
    if f.status == "conflict":
        why.append(f.reasons[0])
        steps.append(_step(f"So sánh cách đo của {', '.join(f.origins)} (phạm vi, quốc gia tính vào, loại doanh thu) "
                           "rồi chọn số hợp với câu hỏi", query=f"{_terms(rep)} {' '.join(f.origins)} methodology",
                           finding=f.key))
    if ONLY_CD in f.reasons:
        why.append(ONLY_CD)
        steps.append(_step("Tìm nguồn hạng A/B (hãng dữ liệu, báo chuyên ngành) cho chỉ số này",
                           query=f"{_terms(rep)} Sensor Tower Newzoo Niko Partners", finding=f.key))
    if all(any(RELAYED in fl for fl in c.flags) for c in cs):
        origins = sorted({c.origin for c in cs})
        notes.append(f"Số của {', '.join(origins)} dẫn lại qua bài viết, chưa đối chiếu bản gốc")
        dom = (load_config()["origins"].get(origins[0]) or {}).get("domain", "")
        steps.append(_step(f"Đối chiếu bản gốc của {origins[0]}" + (f" trên {dom}" if dom else ""),
                           query=f"{origins[0]} {_terms(rep)}", finding=f.key))
    for fl in dict.fromkeys(fl for c in cs for fl in c.flags):
        if not any(w in fl for w in UNCERTAIN_FLAGS):
            continue
        why.append(fl)
        if "ngoài khung" in fl:
            steps.append(_step(f"Tìm số đúng khung thời gian của câu hỏi ({window.label})",
                               query=_terms(rep, period=str(window.end.year)), finding=f.key))
        elif "dự báo" in fl:
            steps.append(_step("Tìm số đã đo thay cho số dự báo", query=f"{_terms(rep)} actual", finding=f.key))
        elif "không phải số của cả" in fl:
            steps.append(_step("Tìm số của cả 12 tháng thay cho số theo quý hoặc nửa năm",
                               query=_terms(rep, period=f"full year {window.end.year - 1}"), finding=f.key))
        elif link:
            steps.append(_step("Mở nguồn tại câu trích để xem lại kỳ đo, phạm vi hoặc giá trị tuyệt đối",
                               url=link, finding=f.key))
    if not why and f.confidence not in ("Cao", "Trung bình"):
        why.append(f"Mức tin cậy {f.confidence}")
    return why, steps, notes


ACTION = {
    "Nên ưu tiên": "Nên làm: ưu tiên phương án trong câu hỏi.",
    "Chưa nên": "Chưa đủ cơ sở để quyết định; bổ sung dữ liệu theo bước dưới đây.",
    "Đã có câu trả lời": "Có thể dùng câu trả lời này làm căn cứ.",
    "Có số liệu nhưng chưa chắc chắn": "Chưa nên dùng các con số này làm căn cứ chính; làm bước dưới đây trước.",
    "Cần thêm dữ liệu": "Chưa đủ căn cứ để quyết định; bổ sung dữ liệu theo bước dưới đây.",
}
CARD_EVIDENCE = 3       # a decision card is read in seconds, not a report


def decision_card(brief: dict, findings: list[Finding], claims: list[Claim], sources: dict[str, Source]) -> dict:
    """Change Request A4: what to do next and which evidence that rests on, picked by code from the brief.
    Evidence is what the kept reasons cite, trusted first, never a figure outside the question's scope."""
    by_id = {c.id: c for c in claims}
    finding = {f.key: f for f in findings}
    status = {x["finding"]: "trusted" for x in brief.get("trusted", [])}
    status.update({x["finding"]: "uncertain" for x in brief.get("uncertain", [])})
    why_map = {x["finding"]: "; ".join(x.get("why", [])) for x in brief.get("uncertain", [])}
    of_claim = {cid: f.key for f in findings for cid in f.claim_ids}
    keys = list(dict.fromkeys(of_claim[i] for x in brief["reasons"] for i in x["claim_ids"] if i in of_claim))
    if brief["decision"] in ("Đã có câu trả lời", "Nên ưu tiên"):
        # Kết luận "Đã có câu trả lời" hay "Nên ưu tiên": hành động là dùng kết luận, bằng chứng lấy từ mục có thể tin
        keys = [k for k in keys if status.get(k) == "trusted"] or [k for k in status if status[k] == "trusted"]
    else:
        keys = [k for k in keys if k in status] or list(status)
    keys.sort(key=lambda k: status[k] != "trusted")
    evidence = []
    for k in keys[:CARD_EVIDENCE]:
        f = finding[k]
        # the copy a reader should open: best tier, and the data firm's own page before an article quoting it
        def best(cs):
            return min(cs, key=lambda c: (c.tier, any(RELAYED in fl for fl in c.flags)))
        c = best([by_id[i] for i in f.claim_ids])
        # one quote per data firm, so a conflict can be checked figure by figure
        links = [{"origin": o, "claim_id": x.id, "value": x.value_text, "url": claim_link(x, sources.get(x.source_id))}
                 for o in f.origins for x in [best([by_id[i] for i in f.claim_ids if by_id[i].origin == o])]]
        evidence.append({"finding": k, "label": f.label, "values": _values(f), "origins": f.origins, "tier": c.tier,
                         "status": status[k], "claim_id": c.id, "quote": c.quote,
                         "url": claim_link(c, sources.get(c.source_id)), "links": links,
                         "why": why_map.get(k, "")})
    steps = brief.get("next_steps", [])
    # the AI's own wording only for a conclusion the code let stand as firm; otherwise the code's instruction
    firm = brief["decision"] in ("Nên ưu tiên", "Đã có câu trả lời")
    action = (brief.get("next_action") if firm else "") or ACTION.get(brief["decision"], ACTION["Cần thêm dữ liệu"])
    return {"action": action, "next_step": steps[0] if steps else None, "evidence": evidence}


def sort_evidence(findings: list[Finding], claims: list[Claim], sources: dict[str, Source], window: Window,
                  question_market: str, gaps: list[str]) -> dict:
    """trusted: answers the question and passes every rule; uncertain: answers it but something is off;
    other: verified but about another period, kept for reference. Next steps are ordered by what matters most."""
    by_id = {c.id: c for c in claims}
    trusted, uncertain, other = [], [], []
    steps, later = [], []
    for f in findings:
        item = {"finding": f.key, "label": f.label, "values": _values(f), "origins": f.origins,
                "confidence": f.confidence, "claim_ids": f.claim_ids}
        off = off_scope(f, by_id[f.claim_ids[0]], window)
        if off:
            other.append({**item, "why": [off]})
            continue
        why, fsteps, notes = judge(f, by_id, sources, window, question_market)
        if why:
            uncertain.append({**item, "why": why + notes, "next_steps": fsteps})
            steps += fsteps
        else:
            trusted.append({**item, "why": f.reasons, "notes": notes})
            later += fsteps
    geo = [x for x in other if "câu hỏi hỏi về" in x["why"][0]]
    if geo and question_market not in ("", "chưa rõ") and not trusted:
        rep = by_id[geo[0]["claim_ids"][0]]
        steps.append(_step(f"Mới có số của thị trường khác, tìm số riêng cho {question_market}",
                           query=_terms(rep, market=question_market)))
    for g in gaps:
        steps.append(_step(f"Chưa có dữ liệu đã kiểm cho tiêu chí \"{g}\"", ask=f"Tìm số liệu cho tiêu chí: {g}"))
    # numbers whose quote was only the number itself: usually a chart, so point the user to the page
    bare = defaultdict(list)
    for c in claims:
        if not c.verified and ("quá ngắn" in c.verify_note or "con số có trong nguồn" in c.verify_note):
            bare[(c.source_id, c.page)].append(c)
    for (sid, page), cs in bare.items():
        s = sources.get(sid)
        if s and len(cs) >= CHART_MIN_NUMBERS:
            where = f"trang {page} của " if page else ""
            # a web page has no pages: jump to the first of those numbers instead
            first = next((c.value_text for c in cs if "con số có trong nguồn" in c.verify_note), cs[0].quote)
            steps.append(_step(f"{len(cs)} con số ở {where}\"{s.title or s.domain}\" chưa kiểm được vì câu trích chỉ có "
                               "con số hoặc nhãn bị ghép với số (thường là biểu đồ): mở để đọc trực tiếp",
                               url=evidence_url(s.url, s.kind, first, page)))
    # the same advice for several findings becomes one step listing them all
    merged: dict[str, dict] = {}
    for s in steps + later:
        k = s["text"]
        if k in merged:
            merged[k]["findings"] += [x for x in s["findings"] if x not in merged[k]["findings"]]
        else:
            merged[k] = {**s, "findings": list(s["findings"])}
    return {"trusted": trusted, "uncertain": uncertain, "other": other, "next_steps": list(merged.values())}
