"""Check every claim against its source with plain code, no LLM.

A claim is kept only if
  1. its quote appears in the source text (after normalising whitespace, punctuation,
     case and decimal marks), and
  2. every digit group of its value appears inside that quote.
Everything else is rejected with a reason the user can read.
"""
from __future__ import annotations

import re

from rapidfuzz import fuzz

from .models import Claim, Source
from .textnorm import normalize, normalize_with_map, number_tokens, numbers_in, value_mismatch

MIN_QUOTE_CHARS = 15
PAGE_RE = re.compile(r"\[\[Trang (\d+)\]\]")

_norm_cache: dict[str, tuple[str, list[int]]] = {}


def _normed(source: Source) -> tuple[str, list[int]]:
    key = f"{source.id}:{len(source.text)}"
    if key not in _norm_cache:
        _norm_cache[key] = normalize_with_map(source.text)
    return _norm_cache[key]


def find_quote(quote: str, source: Source) -> tuple[int, int] | None:
    """Return (start, end) of the quote in source.text, or None."""
    nq = normalize(quote)
    if not nq:
        return None
    nt, idx = _normed(source)
    pos = nt.find(nq)
    if pos < 0:
        return None
    return idx[pos], idx[pos + len(nq) - 1] + 1


def closest_match_score(quote: str, source: Source) -> float:
    nq = normalize(quote)
    nt, _ = _normed(source)
    if not nq or not nt:
        return 0.0
    res = fuzz.partial_ratio_alignment(nq, nt, score_cutoff=60)
    return round(res.score, 1) if res else 0.0


def page_at(text: str, pos: int) -> int | None:
    page = None
    for m in PAGE_RE.finditer(text, 0, pos):
        page = int(m.group(1))
    return page


def verify_claim(claim: Claim, source: Source) -> Claim:
    claim.verified = False
    if not source or not source.text:
        claim.verify_note = "Không có văn bản nguồn để đối chiếu"
        return claim
    if len(normalize(claim.quote)) < MIN_QUOTE_CHARS:
        claim.verify_note = "Câu trích quá ngắn để kiểm"
        span = find_quote(claim.quote, source)
        if span:     # still rejected, but the page lets the user open the chart it came from
            claim.page = page_at(source.text, span[0])
        return claim

    span = find_quote(claim.quote, source)
    if span is None:
        score = closest_match_score(claim.quote, source)
        claim.match_score = score
        if score >= 90:
            claim.verify_note = (f"Không tìm thấy nguyên văn trong nguồn (đoạn giống nhất {score:.0f}%): "
                                 "có thể AI đã chép sai hoặc diễn đạt lại")
        else:
            claim.verify_note = f"Không tìm thấy câu trích trong nguồn (đoạn giống nhất {score:.0f}%)"
        num = find_quote(claim.value_text, source) if numbers_in(claim.value_text, claim.quote) else None
        if num:     # the number is there but not the words around it: usually a chart label stitched to a value
            claim.page = page_at(source.text, num[0])
            claim.verify_note += "; con số có trong nguồn nhưng câu chữ đi kèm thì không (thường do ghép nhãn với số trong biểu đồ)"
        return claim

    claim.match_score = 100.0
    if len(number_tokens(claim.value_text)) > 1:
        claim.verify_note = f"Giá trị \"{claim.value_text}\" có nhiều con số, không rõ số nào là của nhận định"
        return claim
    if not numbers_in(claim.value_text, claim.quote):
        claim.verify_note = f"Giá trị \"{claim.value_text}\" không nằm trong câu trích"
        return claim
    bad = value_mismatch(claim.value_text, claim.quote)
    if bad:
        claim.verify_note = f"Giá trị \"{claim.value_text}\" khác con số trong câu trích về {bad}"
        return claim

    start, end = span
    claim.page = page_at(source.text, start)
    claim.context = source.text[max(0, start - 600): end + 200]
    if claim.section_title and find_quote(claim.section_title, source) is None:
        claim.flags.append("Tiêu đề bảng/chương do AI ghi không có trong nguồn")
        claim.section_title = ""
    claim.verified = True
    claim.verify_note = "Đã tìm thấy câu trích trong nguồn" + (f" (trang {claim.page})" if claim.page else "")
    return claim
