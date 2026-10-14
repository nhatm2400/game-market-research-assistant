"""Data structures shared by the pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Source:
    id: str
    url: str
    title: str = ""
    domain: str = ""
    published: Optional[str] = None      # YYYY-MM-DD if known
    kind: str = "html"                   # html | pdf | upload
    text: str = ""
    error: Optional[str] = None
    tier: str = "D"                      # A | B | C | D after adjustments
    base_tier: str = "D"                 # tier from the domain list only
    tier_notes: list[str] = field(default_factory=list)
    publisher: str = ""                  # who runs the website (domain owner)

    def to_dict(self, with_text: bool = False) -> dict:
        d = asdict(self)
        if not with_text:
            d["text"] = f"<{len(self.text)} ký tự>"
        return d


@dataclass
class Claim:
    id: str
    source_id: str
    claim_text: str
    metric: str                 # revenue | growth | downloads | players | share | rank | other
    value_text: str             # value exactly as written in the quote, e.g. "$625 million"
    market: str
    period: str
    scope: str = "unknown"      # all_games | mobile | mobile_iap | pc_console | unknown
    genre: str = ""
    genre_level: str = "all"    # all | genre | subgenre
    quote: str = ""
    section_title: str = ""
    attributed_to: str = ""
    criterion: int = -1
    # filled by code
    value: Optional[float] = None
    unit: str = ""
    verified: bool = False
    verify_note: str = ""
    match_score: float = 0.0
    page: Optional[int] = None
    context: str = ""
    origin: str = ""
    tier: str = "D"
    flags: list[str] = field(default_factory=list)
    excluded_by_user: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Finding:
    """Verified claims that measure the same thing (same metric, market, period, scope, genre)."""
    key: str
    label: str
    claim_ids: list[str]
    origins: list[str]
    values: list[float]
    unit: str
    status: str                 # agree | single | conflict
    spread_pct: float
    confidence: str             # Cao | Trung bình | Thấp
    reasons: list[str]

    def to_dict(self) -> dict:
        return asdict(self)
