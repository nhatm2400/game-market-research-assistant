"""Parse measurement periods ("Q1 2025", "H1 2026", "2024") and compare them with the
time frame the user asked about. Mismatches become flags."""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date

GRAN_ORDER = ["month", "quarter", "half", "year", "multi"]
GRAN_VI = {"month": "tháng", "quarter": "quý", "half": "nửa năm", "year": "năm", "multi": "nhiều năm"}

MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})


@dataclass
class Span:
    start: date
    end: date
    gran: str


@dataclass
class Window:
    start: date
    end: date
    kind: str      # past12 | future | specific | default
    label: str


def _end_of_month(y: int, m: int) -> date:
    return date(y, m, calendar.monthrange(y, m)[1])


def _add_months(d: date, n: int) -> date:
    y, m = divmod(d.month - 1 + n, 12)
    return date(d.year + y, m + 1, 1)


def _spans(text: str) -> list[Span]:
    s = (text or "").lower()
    spans: list[Span] = []
    used: list[tuple[int, int]] = []

    def take(m, span):
        spans.append(span)
        used.append(m.span())

    def free(m):
        return all(m.end() <= a or m.start() >= b for a, b in used)

    for m in re.finditer(r"(?:\bq|quý\s*|quarter\s*)([1-4])\s*[/ \-,]?\s*(?:of\s*)?((?:19|20)\d{2})", s):
        q, y = int(m.group(1)), int(m.group(2))
        take(m, Span(date(y, 3 * q - 2, 1), _end_of_month(y, 3 * q), "quarter"))
    for m in re.finditer(r"\b((?:19|20)\d{2})\s*[/ \-]?\s*q([1-4])\b", s):
        if free(m):
            y, q = int(m.group(1)), int(m.group(2))
            take(m, Span(date(y, 3 * q - 2, 1), _end_of_month(y, 3 * q), "quarter"))
    for m in re.finditer(r"(?:\bh([12])|\b([12])h|nửa (đầu|cuối)( năm)?|(first|second) half( of)?)\s*[/ \-]?\s*((?:19|20)\d{2})", s):
        if free(m):
            first = (m.group(1) == "1" or m.group(2) == "1" or m.group(3) == "đầu" or m.group(5) == "first")
            y = int(m.group(7))
            take(m, Span(date(y, 1 if first else 7, 1), _end_of_month(y, 6 if first else 12), "half"))
    for m in re.finditer(r"tháng\s*(\d{1,2})\s*[/ \-]\s*((?:19|20)\d{2})", s):
        if free(m) and 1 <= int(m.group(1)) <= 12:
            y, mo = int(m.group(2)), int(m.group(1))
            take(m, Span(date(y, mo, 1), _end_of_month(y, mo), "month"))
    for m in re.finditer(r"\b([a-z]{3,9})\.?\s+((?:19|20)\d{2})\b", s):
        if free(m) and m.group(1) in MONTHS:
            y, mo = int(m.group(2)), MONTHS[m.group(1)]
            take(m, Span(date(y, mo, 1), _end_of_month(y, mo), "month"))
    for m in re.finditer(r"\b((?:19|20)\d{2})-(\d{2})\b", s):
        if free(m) and 1 <= int(m.group(2)) <= 12:
            y, mo = int(m.group(1)), int(m.group(2))
            take(m, Span(date(y, mo, 1), _end_of_month(y, mo), "month"))
    for m in re.finditer(r"(?<!\d)((?:19|20)\d{2})(?!\d)", s):
        if free(m):
            y = int(m.group(1))
            take(m, Span(date(y, 1, 1), date(y, 12, 31), "year"))
    return spans


def parse_period(text: str) -> Span | None:
    spans = _spans(text)
    if not spans:
        return None
    start = min(sp.start for sp in spans)
    end = max(sp.end for sp in spans)
    gran = min((sp.gran for sp in spans), key=GRAN_ORDER.index)
    years = {sp.start.year for sp in spans if sp.gran == "year"}
    if gran == "year" and len(years) > 1 and not re.search(r"\b(vs|so với|compared|yoy)\b", text.lower()):
        gran = "multi"
    return Span(start, end, gran)


PAST12 = r"(12|mười hai) tháng (qua|gần đây|gần nhất|vừa qua|trước)|last (12|twelve) months|past (12 months|year)|năm qua"
FUTURE = r"(12 tháng|năm|thời gian) (tới|sắp tới)|next (12 months|year)|tiềm năng|potential|nên phát hành|should .* (publish|launch)"


def question_window(question: str, today: date | None = None) -> Window:
    today = today or date.today()
    q = (question or "").lower()
    if re.search(PAST12, q):
        return Window(_add_months(date(today.year, today.month, 1), -12), today, "past12", "12 tháng gần nhất")
    sp = parse_period(q)
    if sp:
        return Window(sp.start, sp.end, "specific", f"{sp.start:%m/%Y} đến {sp.end:%m/%Y}")
    if re.search(FUTURE, q):
        return Window(_add_months(date(today.year, today.month, 1), -24), today, "future",
                      "câu hỏi về tương lai, dùng dữ liệu 24 tháng gần nhất")
    return Window(_add_months(date(today.year, today.month, 1), -24), today, "default",
                  "24 tháng gần nhất (mặc định)")


def period_flags(period: str, window: Window, today: date | None = None) -> list[str]:
    today = today or date.today()
    sp = parse_period(period)
    if sp is None:
        return ["Không xác định được kỳ đo"]
    flags = []
    if sp.start > today:
        flags.append("Số dự báo, chưa phải số đã đo")
        return flags
    if sp.end < window.start or sp.start > window.end:
        flags.append(f"Kỳ đo \"{period}\" nằm ngoài khung thời gian của câu hỏi ({window.label})")
    elif window.kind == "past12" and sp.gran in ("month", "quarter", "half"):
        flags.append(f"Số theo {GRAN_VI[sp.gran]}, không phải số của cả 12 tháng")
    return flags
