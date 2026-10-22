"""Compare verified claims, separate "different definition" from
"real conflict", and score confidence with public rules instead of asking the LLM."""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date

from .models import Claim, Finding, Source
from .periods import Window, parse_period, period_flags
from .sources import months_between, parse_date
from .textnorm import fmt_value, parse_value

CONFLICT_THRESHOLD = 0.05   # independent origins differing by more than 5% count as a real conflict

REGION = "Đông Nam Á"
SEA_COUNTRIES = {
    "Việt Nam": ["vietnam", "việt nam", "viet nam"],
    "Indonesia": ["indonesia"],
    "Thái Lan": ["thailand", "thái lan"],
    "Philippines": ["philippines", "philippine"],
    "Malaysia": ["malaysia"],
    "Singapore": ["singapore"],
}
MARKET_ALIASES = {
    REGION: ["southeast asia", "south east asia", "south-east asia", "sea", "sea6", "sea-6", "đông nam á", "asean"],
    "Toàn cầu": ["global", "worldwide", "world", "toàn cầu", "thế giới"],
    **SEA_COUNTRIES,
}
METRIC_VI = {"revenue": "doanh thu", "growth": "tăng trưởng", "downloads": "lượt tải",
             "players": "số người chơi", "share": "thị phần", "rank": "xếp hạng", "other": "chỉ số khác"}
SCOPE_VI = {"all_games": "toàn ngành game", "mobile": "game mobile", "mobile_iap": "IAP game mobile",
            "pc_console": "PC/console", "unknown": "phạm vi chưa rõ"}
CONF_ORDER = ["Thấp", "Trung bình", "Cao"]


def norm_market(m: str) -> str:
    low = (m or "").lower().strip()
    for name, aliases in MARKET_ALIASES.items():
        for a in aliases:
            if re.search(r"(?<![a-z])" + re.escape(a) + r"(?![a-z])", low):
                return name
    return m.strip() or "chưa rõ"


def _countries_in(text: str) -> set[str]:
    low = (text or "").lower()
    return {c for c, al in SEA_COUNTRIES.items() if any(a in low for a in al)}


def _mentions_region(text: str) -> bool:
    low = (text or "").lower()
    return any(re.search(r"(?<![a-z])" + re.escape(a) + r"(?![a-z])", low) for a in MARKET_ALIASES[REGION])


def geo_flags(claim: Claim, question_market: str) -> list[str]:
    flags = []
    market = norm_market(claim.market)
    if market == REGION:
        # the "Vietnam Market Lens" trap: a regional label on a table that is about one country
        heading = claim.section_title
        near = (claim.context or "")[-900:]
        countries = _countries_in(heading) or (_countries_in(near) if not _mentions_region(near[-500:]) else set())
        if len(countries) == 1:
            c = next(iter(countries))
            flags.append(f"Ghi là {REGION} nhưng đoạn/bảng chứa câu trích nói về {c}: cần xem lại phạm vi")
    if question_market and question_market != "chưa rõ" and market not in (question_market, "chưa rõ"):
        flags.append(f"Số của thị trường {market}, câu hỏi hỏi về {question_market}")
    return flags


def stale_forecast_flag(period: str, published: str | None, today: date) -> list[str]:
    """A '2025' figure in an article from 2024 was a forecast when written, even if 2025 is past now;
    one from September 2025 was an estimate for a year not yet over."""
    sp, pub = parse_period(period), parse_date(published)
    if not (sp and pub) or sp.start > today:
        return []
    if pub < sp.start:
        return [f"Số dự báo tại thời điểm đăng (nguồn đăng {pub:%m/%Y}, kỳ đo {period}): chưa chắc là số đã đo"]
    if pub < sp.end and sp.end <= today:
        return [f"Kỳ đo {period} chưa kết thúc khi nguồn đăng ({pub:%m/%Y}): là số ước tính hoặc dự báo, "
                "chưa chắc là số đã đo"]
    return []


def context_flags(claim: Claim, window: Window, question_market: str, today: date) -> list[str]:
    """Flags that depend on the question asked; recomputed when a follow-up changes the question."""
    return period_flags(claim.period, window, today) + geo_flags(claim, question_market)


def enrich_claim(claim: Claim, window: Window, question_market: str, today: date,
                 published: str | None = None) -> Claim:
    claim.value, claim.unit = parse_value(claim.value_text)
    if claim.metric == "revenue" and not claim.unit and claim.value is not None and abs(claim.value) >= 1e6:
        # "5.37 billion" in a market report is USD; without this it would not be compared with "$5.89 billion"
        claim.unit = "USD"
        claim.flags.append("Không ghi đơn vị tiền, coi là USD để so sánh")
    claim.market = norm_market(claim.market)
    claim.flags += context_flags(claim, window, question_market, today)
    claim.flags += stale_forecast_flag(claim.period, published, today)
    if claim.unit == "%" and claim.metric == "growth" and claim.value is not None and abs(claim.value) >= 100:
        claim.flags.append("Tăng trưởng trên 100%: cần xem giá trị tuyệt đối, có thể do nền nhỏ")
    claim.flags = list(dict.fromkeys(claim.flags))
    return claim


def _base_key(c: Claim) -> tuple:
    sp = parse_period(c.period)
    per = f"{sp.start:%Y-%m}..{sp.end:%Y-%m}" if sp else c.period.lower()
    return (c.metric, c.market, per, (c.genre or "").lower().strip(), c.unit)


def _label(c: Claim) -> str:
    g = f", {c.genre}" if c.genre else ""
    return f"{METRIC_VI.get(c.metric, c.metric).capitalize()} {SCOPE_VI.get(c.scope, c.scope)}{g}, {c.market}, {c.period}"


def _infer_scale(good: list[Claim]) -> None:
    """A table cell "5.89" under a "USD billion" header measures the same thing as "$5.89 billion" elsewhere.
    Rescale it only when a USD figure for the same metric, market and period is within a factor of 2."""
    usd: dict[tuple, list[float]] = defaultdict(list)
    for c in good:
        if c.metric == "revenue" and c.unit == "USD" and c.value:
            usd[_base_key(c)[:-1]].append(c.value)
    for c in good:
        refs = usd.get(_base_key(c)[:-1]) if c.metric == "revenue" and not c.unit else None
        if not refs or not c.value or abs(c.value) >= 1e6:
            continue
        for k, name in ((1e9, "tỷ"), (1e6, "triệu")):
            if any(0.5 <= c.value * k / r <= 2 for r in refs):
                c.value, c.unit = c.value * k, "USD"
                c.flags.append(f"Số trong bảng không ghi đơn vị, suy ra là {name} USD từ số cùng chỉ số ở nguồn khác")
                break


def build_findings(claims: list[Claim], sources: dict[str, Source], today: date) -> list[Finding]:
    good = [c for c in claims if c.verified and not c.excluded_by_user and c.value is not None]
    _infer_scale(good)
    known: dict[tuple, set[str]] = defaultdict(set)
    for c in good:
        if c.scope != "unknown":
            known[_base_key(c)].add(c.scope)
    groups: dict[tuple, list[Claim]] = defaultdict(list)
    for c in good:
        scopes = known[_base_key(c)]
        # an unlabelled scope joins the only labelled one measuring the same thing, instead of a duplicate group
        scope = next(iter(scopes)) if c.scope == "unknown" and len(scopes) == 1 else c.scope
        groups[_base_key(c) + (scope,)].append(c)

    findings = []
    for i, (key, cs) in enumerate(groups.items(), 1):
        cs.sort(key=lambda c: c.scope == "unknown")     # label from a claim whose scope is known
        by_origin: dict[str, list[Claim]] = defaultdict(list)
        for c in cs:
            by_origin[c.origin].append(c)
        # one value per independent origin (the best-tier copy of it)
        reps = [min(v, key=lambda c: c.tier) for v in by_origin.values()]
        vals = [c.value for c in reps]
        lo, hi = min(vals), max(vals)
        spread = (hi - lo) / abs(lo) if lo else (0.0 if hi == lo else 1.0)
        if cs[0].unit == "%":
            spread = abs(hi - lo) / max(abs(lo), 1.0)
        status = "single" if len(reps) == 1 else ("conflict" if spread > CONFLICT_THRESHOLD else "agree")

        reasons = []
        good = [c for c in reps if c.tier in ("A", "B")]
        recent = []
        for c in good:
            pub = parse_date(sources[c.source_id].published) if c.source_id in sources else None
            if pub and months_between(pub, today) <= 12:
                recent.append(c)
        if status == "conflict":
            conf = "Thấp"
            if lo < 0 < hi:
                reasons.append("Các nguồn gốc độc lập trái chiều: có nguồn ghi tăng, có nguồn ghi giảm")
            else:
                reasons.append(f"Các nguồn gốc độc lập lệch nhau {spread * 100:.0f}% (ghi dạng khoảng)")
        elif len(good) >= 2 and len(recent) >= 2:
            conf = "Cao"
            reasons.append(f"{len(good)} nguồn gốc độc lập hạng A/B, đăng trong 12 tháng, khớp nhau")
        elif good:
            conf = "Trung bình"
            if len(good) >= 2:
                reasons.append(f"{len(good)} nguồn gốc độc lập hạng A/B nhưng có nguồn đăng quá 12 tháng")
            else:
                reasons.append(f"Chỉ có một nguồn gốc ({good[0].origin}, hạng {good[0].tier})")
        else:
            conf = "Thấp"
            reasons.append("Chỉ có nguồn hạng C hoặc D")
        if len(cs) > len(reps):
            reasons.append(f"{len(cs)} bài viết nhưng chỉ {len(reps)} nguồn gốc")
        serious = [f for c in cs for f in c.flags if "ngoài khung" in f or "cần xem lại phạm vi" in f
                   or "dự báo" in f or "không phải số của cả" in f]
        if serious and conf != "Thấp":
            conf = CONF_ORDER[CONF_ORDER.index(conf) - 1]
            reasons.append("Có cảnh báo về kỳ đo hoặc phạm vi: hạ một mức")

        findings.append(Finding(
            key=f"F{i}", label=_label(cs[0]), claim_ids=[c.id for c in cs],
            origins=sorted(by_origin), values=vals, unit=cs[0].unit, status=status,
            spread_pct=round(spread * 100, 1), confidence=conf, reasons=reasons,
        ))
    _mark_newer(findings, {c.id: c for c in claims}, today)
    return findings


def _mark_newer(findings: list[Finding], claims: dict[str, Claim], today: date) -> None:
    """Same metric, market, scope and genre measured over a later period of the same length:
    the older finding is kept but points to the newer one."""
    groups: dict[tuple, list[tuple]] = defaultdict(list)
    for f in findings:
        c = claims[f.claim_ids[0]]
        sp = parse_period(c.period)
        if c.metric in ("revenue", "downloads", "players", "share") and sp and sp.start <= today:
            groups[(c.metric, c.market, c.scope, (c.genre or "").lower(), c.unit, sp.gran)].append((sp.end, f))
    for items in groups.values():
        newest = max(items, key=lambda x: x[0])
        for end, f in items:
            if end < newest[0]:
                f.newer = newest[1].key


def definition_differences(findings: list[Finding], claims: dict[str, Claim]) -> list[str]:
    """Findings on the same metric and market that differ only in period/scope/genre:
    these look like conflicting numbers but measure different things."""
    notes = []
    by_mm: dict[tuple, list[Finding]] = defaultdict(list)
    for f in findings:
        c = claims[f.claim_ids[0]]
        if c.metric in ("revenue", "downloads", "players"):
            by_mm[(c.metric, c.market)].append(f)
    for (metric, market), fs in by_mm.items():
        if len(fs) < 2:
            continue
        parts = []
        for f in fs:
            c = claims[f.claim_ids[0]]
            vals = " đến ".join(dict.fromkeys(fmt_value(v, f.unit) for v in sorted(f.values)))
            parts.append(f"{vals} ({SCOPE_VI.get(c.scope, c.scope)}, {c.period}{', ' + c.genre if c.genre else ''}; {', '.join(f.origins)})")
        notes.append(f"{METRIC_VI[metric].capitalize()} {market}: " + "; ".join(parts)
                     + ". Các số này khác kỳ đo hoặc phạm vi đo nên không so trực tiếp được.")
    return notes


def overall_confidence(findings: list[Finding], cited: set[str]) -> str:
    fs = [f for f in findings if f.key in cited] or findings
    if not fs:
        return "Chưa đủ dữ liệu"
    levels = [CONF_ORDER.index(f.confidence) for f in fs]
    # a recommendation is as strong as its typical evidence, never stronger than the best
    levels.sort()
    return CONF_ORDER[levels[len(levels) // 2] if len(levels) > 2 else levels[0]]
