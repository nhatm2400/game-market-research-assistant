"""Text normalisation and number parsing used by the quote checker.

Normalisation keeps letters (including Vietnamese) and digits, lowercases them and turns
every other character into a single space. Both the quote and the source go through the
same function, so differences in whitespace, punctuation, curly quotes or decimal marks
do not matter, but any change of words or digits does.
"""
from __future__ import annotations

import re
import unicodedata


def _norm_char(ch: str) -> str:
    if ch.isalnum():
        return ch.lower()
    return " "


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    out = "".join(_norm_char(c) for c in text)
    return re.sub(r" +", " ", out).strip()


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Normalise and keep, for every output char, its index in `text`.

    `text` must already be NFKC (sources are stored that way), so positions in the map
    point straight into the stored source text.
    """
    out: list[str] = []
    idx: list[int] = []
    prev_space = True
    for i, ch in enumerate(text):
        c = _norm_char(ch)
        if c == " ":
            if prev_space:
                continue
            prev_space = True
        else:
            prev_space = False
        for cc in c:            # lower() can return 2 chars (e.g. "İ")
            out.append(cc)
            idx.append(i)
    while out and out[-1] == " ":
        out.pop()
        idx.pop()
    return "".join(out), idx


NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")

_MULT = [
    (r"trillion|nghìn tỷ|ngàn tỷ", 1e12),
    (r"billion|bn|tỷ|tỉ|\bb\b", 1e9),
    (r"million|mn|triệu|\bm\b", 1e6),
    (r"thousand|nghìn|ngàn|\bk\b", 1e3),
]


def number_tokens(text: str) -> list[str]:
    """Digit groups of a value in normalised form, e.g. '$5.37 billion' -> ['5 37']."""
    return [normalize(m.group(0)) for m in NUM_RE.finditer(text or "")]


def parse_number(s: str) -> float | None:
    s = s.strip()
    if re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", s):
        return float(s.replace(",", ""))
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", s):          # 1.234.567,8 (vi style)
        return float(s.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d+,\d+", s):                           # decimal comma
        return float(s.replace(",", "."))
    try:
        return float(s)
    except ValueError:
        return None


def parse_value(value_text: str) -> tuple[float | None, str]:
    """'$5.37 billion' -> (5.37e9, 'USD'); '37.6%' -> (37.6, '%')."""
    vt = (value_text or "").lower()
    m = NUM_RE.search(vt)
    if not m:
        return None, ""
    num = parse_number(m.group(0))
    if num is None:
        return None, ""
    if "-" in vt[: m.start()] or "−" in vt[: m.start()]:
        num = -num
    rest = vt[m.end():]
    if "%" in vt or "percent" in vt or "phần trăm" in vt:
        return num, "%"
    mult = 1.0
    for pat, k in _MULT:
        if re.search(pat, rest[:15]):
            mult = k
            break
    unit = "USD" if ("$" in vt or "usd" in vt or "đô" in vt) else ("VND" if ("vnd" in vt or "đồng" in vt) else "")
    return num * mult, unit


def numbers_in(value_text: str, quote: str) -> bool:
    """True if every digit group of value_text appears as a whole token in the quote."""
    toks = number_tokens(value_text)
    if not toks:
        return False
    q = f" {re.sub(r'(?<=[0-9])(?=[^\W\d_])|(?<=[^\W\d_])(?=[0-9])', ' ', normalize(quote))} "   # "9 2m" -> "9 2 m"
    return all(f" {t} " in q for t in toks)


def fmt_value(v: float | None, unit: str) -> str:
    if v is None:
        return "?"
    if unit == "%":
        return f"{v:+.1f}%".replace(".", ",")
    for k, name in [(1e9, "tỷ"), (1e6, "triệu"), (1e3, "nghìn")]:
        if abs(v) >= k:
            num = f"{v / k:.2f}".rstrip("0").rstrip(".")
            return f"{num} {name} {unit}".replace(".", ",").strip()
    return f"{v:g} {unit}".strip()
