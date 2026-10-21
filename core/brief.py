"""The one-page decision brief.

The LLM only writes from verified claims and must cite claim ids. Code then checks every
sentence: a reason without a valid claim id, or with a number that is not in the cited
claims, is dropped and logged. Confidence comes from analyze.py, not from the LLM.
"""
from __future__ import annotations

import re

from .analyze import overall_confidence
from .evidence import sort_evidence
from .llm import LLM
from .models import Claim, Finding, Source
from .periods import Window
from .textnorm import NUM_RE, fmt_value, normalize

DECISIONS = ["Nên ưu tiên", "Chưa nên", "Đã có câu trả lời", "Cần thêm dữ liệu"]

BRIEF_SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": DECISIONS},
        "summary": {"type": "string"},
        "reasons": {"type": "array", "items": {
            "type": "object",
            "properties": {"text": {"type": "string"}, "claim_ids": {"type": "array", "items": {"type": "string"}}},
            "required": ["text", "claim_ids"]}},
        "what_would_change": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["decision", "summary", "reasons", "what_would_change"],
}

BRIEF_PROMPT = """Bạn viết bản tóm tắt quyết định một trang cho chuyên viên phát triển kinh doanh của nhà phát hành game.
Câu hỏi: "{question}"
Khung thời gian dữ liệu: {window}
Tiêu chí: {criteria}

Các nhận định ĐÃ KIỂM CHỨNG (chỉ được dùng những nhận định này):
{claims}

Nhóm số liệu và mức tin cậy do code tính:
{findings}

Khác biệt định nghĩa đã phát hiện:
{defs}

Tiêu chí chưa có dữ liệu: {gaps}

Yêu cầu:
- decision: với câu hỏi có nên làm hay không, chọn "Nên ưu tiên" hoặc "Chưa nên"; với câu hỏi tra cứu một con số
  hoặc sự kiện, chọn "Đã có câu trả lời" nếu các nhận định trả lời được câu hỏi (kể cả khi còn chưa chắc chắn, khi đó
  nói rõ trong summary). Chọn "Cần thêm dữ liệu" khi bằng chứng không đủ để trả lời hoặc để quyết định.
- summary: 1 đến 2 câu tiếng Việt trả lời thẳng câu hỏi, nói rõ điều gì có thể tin và điều gì còn chưa chắc chắn
  (theo trạng thái code đã gán cho từng nhận định).
- reasons: 3 đến 5 lý do. Mỗi lý do gắn claim_ids là mã nhận định làm căn cứ (ví dụ ["C3"]). Mọi con số trong
  lý do phải lấy đúng từ nhận định được gắn mã; không tự tính, không thêm số ngoài danh sách. Nếu số liệu có cảnh báo
  (ngoài khung thời gian, số theo quý, phạm vi địa lý, nền nhỏ) thì nói cảnh báo đó trong lý do.
- what_would_change: 1 đến 3 điều nếu biết thêm sẽ làm thay đổi khuyến nghị, ví dụ dữ liệu còn thiếu.
Viết tiếng Việt tự nhiên, ngắn gọn."""


def _claim_line(c: Claim, finding_of: dict[str, Finding], status_of: dict[str, str]) -> str:
    f = finding_of.get(c.id)
    warn = f" Cảnh báo: {'; '.join(c.flags)}." if c.flags else ""
    status = status_of.get(f.key, "chưa chắc chắn") if f else "chưa chắc chắn"
    return (f"[{c.id}] {c.claim_text} Giá trị: {c.value_text}. Kỳ: {c.period}. Thị trường: {c.market}. "
            f"Nguồn gốc: {c.origin}, hạng {c.tier}. Nhóm {f.key if f else '-'}, trạng thái: {status}.{warn}")


def _finding_line(f: Finding) -> str:
    vals = ", ".join(fmt_value(v, f.unit) for v in f.values)
    return f"{f.key}: {f.label} | giá trị theo nguồn gốc: {vals} | {f.status} | tin cậy {f.confidence} ({'; '.join(f.reasons)})"


def _allowed_numbers(claims: list[Claim], extra: str = "") -> set[str]:
    allowed = {normalize(m.group(0)) for m in NUM_RE.finditer(extra)}
    for c in claims:
        for t in (c.value_text, c.quote, c.period):
            allowed.update(normalize(m.group(0)) for m in NUM_RE.finditer(t or ""))
    return allowed


def unsupported_numbers(text: str, claims: list[Claim], extra: str = "") -> list[str]:
    """Numbers in `text` that are in none of the claims. `extra` is text whose numbers are also allowed:
    the question and its time frame, so "12 tháng" is not mistaken for an invented figure."""
    allowed = _allowed_numbers(claims, extra)
    bad = []
    for m in NUM_RE.finditer(text or ""):
        tok = normalize(m.group(0))
        if len(tok) == 1:            # single digits: counts like "3 nguồn", quarter numbers
            continue
        if tok not in allowed:
            bad.append(m.group(0))
    return bad


def criteria_gaps(criteria: list[str], claims: list[Claim]) -> list[str]:
    covered = {c.criterion for c in claims if c.verified and not c.excluded_by_user}
    return [crit for i, crit in enumerate(criteria) if i not in covered]


def write_brief(llm: LLM | None, question: str, criteria: list[str], claims: list[Claim],
                findings: list[Finding], def_notes: list[str], window: Window,
                sources: dict[str, Source] | None = None, question_market: str = "") -> dict:
    good = [c for c in claims if c.verified and not c.excluded_by_user]
    gaps = criteria_gaps(criteria, claims)
    finding_of = {cid: f for f in findings for cid in f.claim_ids}
    ev = sort_evidence(findings, claims, sources or {}, window, question_market, gaps)
    status_of = {x["finding"]: "có thể tin" for x in ev["trusted"]}
    status_of.update({x["finding"]: "chưa chắc chắn (" + "; ".join(x["why"]) + ")" for x in ev["uncertain"]})
    asked = f"{question} {window.label}"      # numbers the user wrote are not invented by the LLM
    brief = {"decision": "Cần thêm dữ liệu", "summary": "", "reasons": [], "what_would_change": [],
             "confidence": "Chưa đủ dữ liệu", "gaps": gaps, "conflicts": [], "definition_notes": def_notes,
             "guard_log": [], **ev}
    for f in findings:
        if f.status == "conflict":
            brief["conflicts"].append(
                f"{f.label}: {' đến '.join(fmt_value(v, f.unit) for v in sorted(f.values))} "
                f"(lệch {f.spread_pct:.0f}%, nguồn gốc: {', '.join(f.origins)})")

    if not good or llm is None:
        brief["summary"] = ("Chưa đủ dữ liệu đã kiểm chứng để trả lời câu hỏi. "
                            "Không có nhận định nào vừa liên quan vừa tìm thấy câu trích trong nguồn.")
        brief["what_would_change"] = ["Tải lên báo cáo đã mua hoặc thêm link nguồn gốc của hãng dữ liệu"]
        return brief

    out = llm.json(BRIEF_PROMPT.format(
        question=question, window=window.label,
        criteria="; ".join(f"{i}. {c}" for i, c in enumerate(criteria)),
        claims="\n".join(_claim_line(c, finding_of, status_of) for c in good),
        findings="\n".join(_finding_line(f) for f in findings) or "(không có)",
        defs="\n".join(def_notes) or "(không có)",
        gaps="; ".join(gaps) or "(không có)"), BRIEF_SCHEMA)

    by_id = {c.id: c for c in good}
    cited_findings: set[str] = set()
    for r in out.get("reasons", []):
        ids = [i for i in r.get("claim_ids", []) if i in by_id]
        text = r.get("text", "").strip()
        if not ids:
            brief["guard_log"].append(f"Bỏ lý do không gắn mã nhận định hợp lệ: \"{text}\"")
            continue
        bad = unsupported_numbers(text, [by_id[i] for i in ids], asked)
        if bad:
            brief["guard_log"].append(f"Bỏ lý do có số không nằm trong nhận định được trích ({', '.join(bad)}): \"{text}\"")
            continue
        keys = {finding_of[i].key for i in ids if i in finding_of}
        # a reason is only as solid as its weakest cited finding
        trusted = bool(keys) and all(status_of.get(k) == "có thể tin" for k in keys)
        brief["reasons"].append({"text": text, "claim_ids": ids, "status": "trusted" if trusted else "uncertain"})
        cited_findings.update(keys)

    summary = out.get("summary", "").strip()
    bad = unsupported_numbers(summary, good, asked)
    if bad:
        brief["guard_log"].append(f"Bỏ câu tóm tắt có số không có trong nhận định ({', '.join(bad)}): \"{summary}\"")
        summary = ""
    brief["summary"] = summary
    for w in out.get("what_would_change", []):
        if unsupported_numbers(w, good, asked):
            brief["guard_log"].append(f"Bỏ ý có số không có nguồn: \"{w}\"")
        else:
            brief["what_would_change"].append(w)

    brief["decision"] = out.get("decision") if out.get("decision") in DECISIONS else "Cần thêm dữ liệu"
    if brief["reasons"]:
        brief["confidence"] = overall_confidence(findings, cited_findings)
    else:
        brief["decision"] = "Cần thêm dữ liệu"
    if gaps and brief["confidence"] == "Cao":
        brief["confidence"] = "Trung bình"
        brief["guard_log"].append("Hạ mức tin cậy chung xuống Trung bình vì còn tiêu chí chưa có dữ liệu")
    return brief
