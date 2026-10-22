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


# checked in order: "S$" and "Rp" must not be read as US dollars
CURRENCIES = [("SGD", r"s\$|sgd"), ("IDR", r"\brp\.?\s?\d|idr|rupiah"), ("THB", r"thb|฿|baht"),
              ("PHP", r"\bphp|₱|peso"), ("MYR", r"myr|ringgit|\brm\s?\d"), ("VND", r"vnd|đồng|₫"),
              ("USD", r"\$|usd|đô")]


def number_tokens(text: str) -> list[str]:
    """Digit groups of a value in normalised form, e.g. '$5.37 billion' -> ['5 37']."""
    return [normalize(m.group(0)) for m in NUM_RE.finditer(text or "")]


def parse_number(s: str) -> float | None:
    s = s.strip()
    # a thousands group never starts with 0, so "0.817" is a decimal, not 817
    if re.fullmatch(r"[1-9]\d{0,2}(,\d{3})+(\.\d+)?", s):
        return float(s.replace(",", ""))
    if re.fullmatch(r"[1-9]\d{0,2}(\.\d{3})+(,\d+)?", s):     # 1.234.567,8 (vi style)
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
    # a minus sign must sit right before the number: "S-5.89" (table label S) and "year-on-year" are not negative
    pre = vt[: m.start()].rstrip(" $")
    if pre.endswith(("-", "−")) and not pre[:-1][-1:].isalnum():
        num = -num
    rest = vt[m.end():]
    if "%" in vt or "percent" in vt or "phần trăm" in vt:
        return num, "%"
    mult = 1.0
    for pat, k in _MULT:
        if re.search(pat, rest[:15]):
            mult = k
            break
    unit = next((code for code, pat in CURRENCIES if re.search(pat, vt)), "")
    return num * mult, unit


def numbers_in(value_text: str, quote: str) -> bool:
    """True if every digit group of value_text appears as a whole token in the quote."""
    toks = number_tokens(value_text)
    if not toks:
        return False
    q = f" {re.sub(r'(?<=[0-9])(?=[^\W\d_])|(?<=[^\W\d_])(?=[0-9])', ' ', normalize(quote))} "   # "9 2m" -> "9 2 m"
    return all(f" {t} " in q for t in toks)


DECLINE_RE = re.compile(r"declin|decreas|drop|fell|fall|down|lower|shr[iau]nk|contract|negative|loss|giảm|sụt|lỗ", re.I)


def value_mismatch(value_text: str, quote: str) -> str:
    """Why the value disagrees with the same digits in the quote ("" if it does not), e.g. '-8%' for 'grew 8%'.

    Each number in the quote is read with the sign right before it and the words right after it. A quote number
    without a scale word (a table cell under "USD bn") accepts any scale, so only an explicit conflict is rejected.
    """
    v, u = parse_value(value_text)
    m = NUM_RE.search(value_text or "")
    if v is None or not m:
        return ""
    tok = normalize(m.group(0))
    found = list(NUM_RE.finditer(quote or ""))
    why = ""
    for k, q in enumerate(found):
        if normalize(q.group(0)) != tok:
            continue
        end = found[k + 1].start() if k + 1 < len(found) else len(quote)
        sign = re.sub(r"^.*\d", "", quote[max(0, q.start() - 2): q.start()])   # never borrow digits of the number before
        qv, qu = parse_value(sign + quote[q.start(): min(end, q.end() + 15)])
        if qv is None:
            return ""
        if (u == "%" and qu not in ("", "%")) or (u != "%" and qu == "%"):
            why = "đơn vị"
        elif u != "%" and abs(qv) != parse_number(q.group(0)) and abs(abs(v) - abs(qv)) > 1e-6 * abs(v):
            why = "bậc (tỷ, triệu...)"
        elif v < 0 and qv >= 0 and not DECLINE_RE.search(quote):
            why = "dấu"
        else:
            return ""          # one occurrence of the digits agrees with the value
    return why


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
