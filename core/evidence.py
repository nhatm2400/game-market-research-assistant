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
from .periods import Window
from .sources import load_config
from .textnorm import fmt_value

UNCERTAIN_FLAGS = ("ngoài khung", "cần xem lại phạm vi", "dự báo", "không phải số của cả", "câu hỏi hỏi về",
                   "Không xác định được kỳ đo", "Tăng trưởng trên 100%")
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
    return {"text": text, "query": query, "ask": ask, "url": url, "finding": finding}


def _values(f: Finding) -> str:
    return " đến ".join(dict.fromkeys(fmt_value(v, f.unit) for v in sorted(f.values)))


def judge(f: Finding, claims: dict[str, Claim], sources: dict[str, Source], window: Window,
          question_market: str) -> tuple[list[str], list[dict]]:
    """Return (why this finding is uncertain, next steps). No reasons means it can be trusted."""
    cs = [claims[i] for i in f.claim_ids]
    rep = cs[0]
    why, steps = [], []
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
        why.append(f"Chỉ có bài dẫn lại số của {', '.join(origins)}, chưa đối chiếu bản gốc")
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
        elif "câu hỏi hỏi về" in fl and question_market not in ("", "chưa rõ"):
            steps.append(_step(f"Tìm số riêng cho {question_market}", query=_terms(rep, market=question_market),
                               finding=f.key))
        elif "không phải số của cả" in fl:
            steps.append(_step("Tìm số của cả 12 tháng thay cho số theo quý hoặc nửa năm",
                               query=_terms(rep, period=f"full year {window.end.year - 1}"), finding=f.key))
        elif link:
            steps.append(_step("Mở nguồn tại câu trích để xem lại kỳ đo, phạm vi hoặc giá trị tuyệt đối",
                               url=link, finding=f.key))
    if f.newer:
        why.append(f"Đã có số mới hơn cho cùng chỉ số ({f.newer})")
    if not why and f.confidence not in ("Cao", "Trung bình"):
        why.append(f"Mức tin cậy {f.confidence}")
    return why, steps


def sort_evidence(findings: list[Finding], claims: list[Claim], sources: dict[str, Source], window: Window,
                  question_market: str, gaps: list[str]) -> dict:
    by_id = {c.id: c for c in claims}
    trusted, uncertain, steps = [], [], []
    for f in findings:
        why, fsteps = judge(f, by_id, sources, window, question_market)
        item = {"finding": f.key, "label": f.label, "values": _values(f), "origins": f.origins,
                "confidence": f.confidence, "claim_ids": f.claim_ids}
        if why:
            uncertain.append({**item, "why": why, "next_steps": fsteps})
            steps += fsteps
        else:
            trusted.append({**item, "why": f.reasons})
    for g in gaps:
        steps.append(_step(f"Chưa có dữ liệu đã kiểm cho tiêu chí \"{g}\"", ask=f"Tìm số liệu cho tiêu chí: {g}"))
    # numbers whose quote was only the number itself: usually a chart, so point the user to the page
    bare = defaultdict(list)
    for c in claims:
        if not c.verified and "quá ngắn" in c.verify_note:
            bare[(c.source_id, c.page)].append(c.id)
    for (sid, page), ids in bare.items():
        s = sources.get(sid)
        if s and len(ids) >= CHART_MIN_NUMBERS:
            where = f"trang {page} của " if page else ""
            steps.append(_step(f"{len(ids)} con số ở {where}\"{s.title or s.domain}\" chưa kiểm được vì câu trích chỉ có "
                               "con số (thường là biểu đồ): mở để đọc trực tiếp", url=evidence_url(s.url, s.kind, "", page)))
    seen, unique = set(), []
    for s in steps:
        k = s["query"] or s["ask"] or s["url"] or s["text"]
        if k not in seen:
            seen.add(k)
            unique.append(s)
    return {"trusted": trusted, "uncertain": uncertain, "next_steps": unique}
