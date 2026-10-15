"""Rule-based source tiers and origin tracing."""
from __future__ import annotations

import re
from datetime import date
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import yaml

from .models import Claim, Source

TIERS = ["A", "B", "C", "D"]
CONFIG_PATH = Path(__file__).resolve().parent.parent / "data" / "source_tiers.yaml"


@lru_cache(maxsize=1)
def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def domain_of(url: str) -> str:
    host = urlparse(url).netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def _matches(domain: str, entry: str) -> bool:
    return domain == entry or domain.endswith("." + entry)


def base_tier(domain: str) -> tuple[str, str]:
    """Most specific matching entry wins, so a B-listed substack beats C-listed substack.com."""
    cfg = load_config()
    best = None
    for tier in TIERS:
        for entry in cfg.get(tier, []) or []:
            if _matches(domain, entry) and (best is None or len(entry) > len(best[1])):
                best = (tier, entry)
    if best:
        return best[0], f"{best[1]} nằm trong danh sách hạng {best[0]}"
    return "C", "Tên miền không có trong danh sách, mặc định hạng C"


def downgrade(tier: str) -> str:
    return TIERS[min(TIERS.index(tier) + 1, len(TIERS) - 1)]


def months_between(d1: date, d2: date) -> int:
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)


def parse_date(s: str | None) -> date | None:
    if not s:
        return None
    m = re.match(r"(\d{4})-(\d{2})(?:-(\d{2}))?", s)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1))
    except ValueError:
        return None


def origin_by_domain(domain: str) -> str | None:
    for name, info in load_config()["origins"].items():
        if info.get("domain") and _matches(domain, info["domain"]):
            return name
    return None


def assess_source(source: Source, today: date | None = None, upload_tier: str = "B") -> Source:
    today = today or date.today()
    notes: list[str] = []
    if source.kind == "upload":
        tier, why = upload_tier, f"Tài liệu người dùng tải lên, người dùng chọn hạng {upload_tier}"
        source.domain = source.domain or "tải lên"
    else:
        source.domain = source.domain or domain_of(source.url)
        tier, why = base_tier(source.domain)
    source.base_tier = tier
    notes.append(why)
    source.publisher = origin_by_domain(source.domain) or source.domain

    pub = parse_date(source.published)
    if source.kind != "upload":
        if pub is None:
            if tier != "D":
                tier = downgrade(tier)
            notes.append("Không rõ ngày đăng: hạ một hạng")
        else:
            age = months_between(pub, today)
            if age > 24:
                tier = downgrade(tier)
                notes.append(f"Đăng cách đây {age} tháng (quá 24 tháng): hạ một hạng")
            elif age > 12:
                notes.append(f"Đăng cách đây {age} tháng (12 đến 24 tháng)")
            else:
                notes.append(f"Đăng cách đây {max(age, 0)} tháng")
    source.tier = tier
    source.tier_notes = notes
    return source


def _alias_hits(text: str) -> list[tuple[int, str]]:
    hits = []
    low = (text or "").lower()
    for name, info in load_config()["origins"].items():
        for alias in info.get("aliases", []):
            for m in re.finditer(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", low):
                hits.append((m.start(), name))
    return hits


def detect_origin(claim: Claim, source: Source) -> str:
    """Who produced the number: the data firm the article cites, or the publisher itself."""
    if claim.attributed_to:
        hits = _alias_hits(claim.attributed_to)
        if hits:
            return hits[0][1]
    hits = _alias_hits(claim.quote)
    if hits:
        return hits[0][1]
    # look backwards from the quote in its context for the nearest firm name
    ctx = claim.context or ""
    qpos = ctx.lower().find(claim.quote[:30].lower()) if claim.quote else -1
    before = ctx[:qpos] if qpos > 0 else ctx[:600]
    hits = _alias_hits(before[-400:])
    if hits:
        return max(hits)[1]
    return source.publisher or source.domain


def assess_claim(claim: Claim, source: Source) -> Claim:
    claim.origin = detect_origin(claim, source)
    claim.tier = source.tier
    if claim.origin != source.publisher and claim.origin in load_config()["origins"]:
        claim.flags.append(f"Số liệu của {claim.origin}, dẫn lại qua {source.domain}; chưa đối chiếu bản gốc")
    return claim
