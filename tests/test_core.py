"""Deterministic tests for the code-only checks (no network, no API key).

The source texts below are short fixtures written for the tests. The two sentences about
Sensor Tower and Niko Partners are copied from the public pages cited in the Mission 1 report.
"""
from datetime import date

from core.analyze import build_findings, definition_differences, enrich_claim, norm_market
from core.brief import unsupported_numbers, write_brief
from core.models import Claim, Source
from core.periods import parse_period, period_flags, question_window
from core.sources import assess_claim, assess_source, base_tier
from core.textnorm import parse_value
from core.verify import verify_claim

TODAY = date(2026, 10, 13)

ST_TEXT = ("Southeast Asia Mobile Gaming 2025\n"
           "SEA currently ranks seventh globally in in-app purchase (IAP) revenue at $625 million in Q1 2025, "
           "while downloads reached 1.9 billion.\n")
NIKO_TEXT = ("According to Niko Partners, the Southeast Asia games market generated $5.37 billion in revenue "
             "in 2024 across Indonesia, Malaysia, Philippines, Singapore, Thailand and Vietnam.")
STATISTA_TEXT = "Statista estimates that revenue in the SEA-6 games market amounted to $5.89 billion in 2024."
VN_TEXT = ("[[Trang 13]]\n02 VIETNAM MARKET LENS\nTop subgenres by revenue growth in Vietnam\n"
           "Shooter $9.2M 5.2% +579.4%\n")


def src(sid, url, text, published="2025-05-20"):
    return Source(id=sid, url=url, text=text, published=published)


def claim(cid, sid, quote, value_text, **kw):
    base = dict(claim_text="x", metric="revenue", market="Southeast Asia", period="2024", scope="all_games")
    base.update(kw)
    return Claim(id=cid, source_id=sid, quote=quote, value_text=value_text, **base)


# ---- quote verification ----

def test_exact_quote_is_verified_even_with_different_spacing_and_quotes():
    s = src("S1", "https://sensortower.com/blog/x", ST_TEXT)
    c = claim("C1", "S1", "SEA currently ranks seventh globally in in-app purchase (IAP) revenue at $625  million in Q1 2025",
              "$625 million", scope="mobile_iap", period="Q1 2025")
    assert verify_claim(c, s).verified


def test_fabricated_quote_is_rejected():
    s = src("S1", "https://sensortower.com/blog/x", ST_TEXT)
    c = claim("C2", "S1", "SEA mobile game revenue grew 40% year over year in 2025", "40%", metric="growth")
    v = verify_claim(c, s)
    assert not v.verified and "Không tìm thấy" in v.verify_note


def test_paraphrased_quote_is_rejected_with_near_match_score():
    s = src("S1", "https://sensortower.com/blog/x", ST_TEXT)
    c = claim("C3", "S1", "SEA ranks seventh globally in in-app purchase (IAP) revenue at $625 million in Q1 2025",
              "$625 million")
    v = verify_claim(c, s)
    assert not v.verified and v.match_score >= 90


def test_value_not_in_quote_is_rejected():
    s = src("S1", "https://sensortower.com/blog/x", ST_TEXT)
    c = claim("C4", "S1", "SEA currently ranks seventh globally in in-app purchase (IAP) revenue at $625 million in Q1 2025",
              "$652 million")
    v = verify_claim(c, s)
    assert not v.verified and "không nằm trong câu trích" in v.verify_note


def test_value_glued_to_unit_letter_is_found():
    s = src("S9", "https://investgame.net/r.pdf", VN_TEXT)
    c = claim("C8", "S9", "Shooter $9.2M 5.2% +579.4%", "$9.2M")
    assert verify_claim(c, s).verified


def test_page_number_is_recorded_for_pdf_text():
    s = src("S9", "https://investgame.net/r.pdf", VN_TEXT)
    c = claim("C5", "S9", "Shooter $9.2M 5.2% +579.4%", "+579.4%", metric="growth")
    assert verify_claim(c, s).page == 13


# ---- values and periods ----

def test_parse_values():
    assert parse_value("$5.37 billion") == (5.37e9, "USD")
    assert parse_value("$625 million") == (625e6, "USD")
    assert parse_value("5,37 tỷ USD") == (5.37e9, "USD")
    assert parse_value("+37.6%") == (37.6, "%")
    assert parse_value("-17.1%") == (-17.1, "%")


def test_parse_periods():
    assert parse_period("Q1 2025").gran == "quarter"
    sp = parse_period("Q1 2025 vs Q4 2024")
    assert sp.start == date(2024, 10, 1) and sp.end == date(2025, 3, 31)
    assert parse_period("H1 2026").end == date(2026, 6, 30)
    assert parse_period("quý 1/2025").start == date(2025, 1, 1)
    assert parse_period("2024").gran == "year"


def test_quarter_data_is_flagged_for_a_12_month_question():
    w = question_window("Thể loại nào tăng trưởng nhanh nhất 12 tháng qua?", TODAY)
    assert w.kind == "past12"
    assert any("ngoài khung" in f for f in period_flags("Q1 2025 vs Q4 2024", w, TODAY))
    assert any("không phải số của cả 12 tháng" in f for f in period_flags("H1 2026", w, TODAY))


def test_forecast_is_flagged():
    w = question_window("Quy mô thị trường game Đông Nam Á", TODAY)
    assert period_flags("2029", w, TODAY) == ["Số dự báo, chưa phải số đã đo"]


# ---- source tiers and origins ----

def test_tiers_from_list():
    assert base_tier("sensortower.com")[0] == "A"
    assert base_tier("gamedevreports.substack.com")[0] == "B"
    assert base_tier("someone.substack.com")[0] == "C"
    assert base_tier("mordorintelligence.com")[0] == "D"
    assert base_tier("unknown-blog.net")[0] == "C"


def test_old_or_undated_sources_are_downgraded():
    old = assess_source(src("S1", "https://sensortower.com/a", ST_TEXT, "2022-01-01"), TODAY)
    assert old.tier == "B"
    undated = assess_source(src("S2", "https://gamesindustry.biz/a", ST_TEXT, None), TODAY)
    assert undated.tier == "C"


def test_rereported_number_is_traced_to_its_origin():
    s = assess_source(src("S3", "https://gamesbeat.com/niko", NIKO_TEXT, "2025-09-30"), TODAY)
    c = claim("C6", "S3", "the Southeast Asia games market generated $5.37 billion in revenue in 2024",
              "$5.37 billion")
    verify_claim(c, s)
    assess_claim(c, s)
    assert c.origin == "Niko Partners" and c.tier == "B"
    assert any("dẫn lại" in f for f in c.flags)


# ---- conflicts vs different definitions ----

def _verified(cid, s, quote, value_text, **kw):
    c = claim(cid, s.id, quote, value_text, **kw)
    verify_claim(c, s)
    assess_claim(c, s)
    w = question_window("Quy mô thị trường game Đông Nam Á năm 2024", TODAY)
    return enrich_claim(c, w, "Đông Nam Á", TODAY)


def test_real_conflict_vs_definition_difference():
    niko = assess_source(src("S3", "https://gamesbeat.com/niko", NIKO_TEXT, "2025-09-30"), TODAY)
    sta = assess_source(src("S4", "https://statista.com/x", STATISTA_TEXT, "2025-02-10"), TODAY)
    st = assess_source(src("S1", "https://sensortower.com/blog/x", ST_TEXT, "2025-05-20"), TODAY)
    cs = [
        _verified("C1", niko, "the Southeast Asia games market generated $5.37 billion in revenue in 2024", "$5.37 billion"),
        _verified("C2", sta, "revenue in the SEA-6 games market amounted to $5.89 billion in 2024", "$5.89 billion"),
        _verified("C3", st, "SEA currently ranks seventh globally in in-app purchase (IAP) revenue at $625 million in Q1 2025",
                  "$625 million", scope="mobile_iap", period="Q1 2025"),
    ]
    assert all(c.verified for c in cs)
    findings = build_findings(cs, {s.id: s for s in (niko, sta, st)}, TODAY)
    conflict = [f for f in findings if f.status == "conflict"]
    assert len(conflict) == 1 and set(conflict[0].origins) == {"Niko Partners", "Statista"}
    assert conflict[0].confidence == "Thấp"
    notes = definition_differences(findings, {c.id: c for c in cs})
    assert notes and "không so trực tiếp" in notes[0]


def test_same_origin_counts_once():
    a = assess_source(src("S3", "https://gamesbeat.com/niko", NIKO_TEXT, "2025-09-30"), TODAY)
    b = assess_source(src("S5", "https://gamedevreports.substack.com/niko", NIKO_TEXT, "2025-10-31"), TODAY)
    q = "the Southeast Asia games market generated $5.37 billion in revenue in 2024"
    cs = [_verified("C1", a, q, "$5.37 billion"), _verified("C2", b, q, "$5.37 billion")]
    f = build_findings(cs, {a.id: a, b.id: b}, TODAY)[0]
    assert f.origins == ["Niko Partners"] and f.confidence == "Trung bình"


def test_vietnam_table_labelled_as_sea_is_flagged():
    s = assess_source(src("S9", "https://investgame.net/r.pdf", VN_TEXT, "2026-09-03"), TODAY)
    c = claim("C7", "S9", "Shooter $9.2M 5.2% +579.4%", "+579.4%", metric="growth", period="H1 2026",
              section_title="02 VIETNAM MARKET LENS", genre="Shooter", genre_level="subgenre")
    verify_claim(c, s)
    assess_claim(c, s)
    enrich_claim(c, question_window("Thể loại nào tiềm năng ở Đông Nam Á?", TODAY), "Đông Nam Á", TODAY)
    assert any("Việt Nam" in f for f in c.flags)
    assert any("nền nhỏ" in f for f in c.flags)


def test_market_names():
    assert norm_market("SEA-6") == "Đông Nam Á"
    assert norm_market("Vietnam") == "Việt Nam"


# ---- brief guard ----

class FakeLLM:
    calls = 0

    def __init__(self, out):
        self.out = out

    def json(self, prompt, schema):
        self.calls += 1
        return self.out


def test_brief_drops_reasons_with_invented_numbers_or_no_citation():
    st = assess_source(src("S1", "https://sensortower.com/blog/x", ST_TEXT, "2025-05-20"), TODAY)
    c = _verified("C1", st, "SEA currently ranks seventh globally in in-app purchase (IAP) revenue at $625 million in Q1 2025",
                  "$625 million", scope="mobile_iap", period="Q1 2025", criterion=0)
    findings = build_findings([c], {st.id: st}, TODAY)
    fake = FakeLLM({
        "decision": "Nên ưu tiên",
        "summary": "Thị trường đạt 625 triệu USD trong quý 1/2025.",
        "reasons": [
            {"text": "Doanh thu IAP quý 1/2025 là 625 triệu USD.", "claim_ids": ["C1"]},
            {"text": "Thị trường tăng 40% mỗi năm.", "claim_ids": ["C1"]},
            {"text": "Người chơi Đông Nam Á rất thích game mobile.", "claim_ids": []},
        ],
        "what_would_change": ["Có số của cả năm 2025"],
    })
    w = question_window("Quy mô thị trường game Đông Nam Á", TODAY)
    b = write_brief(fake, "Quy mô thị trường game Đông Nam Á", ["Quy mô", "Tăng trưởng"], [c], findings, [], w)
    assert [r["text"] for r in b["reasons"]] == ["Doanh thu IAP quý 1/2025 là 625 triệu USD."]
    assert len(b["guard_log"]) == 2
    assert b["gaps"] == ["Tăng trưởng"]
    assert b["confidence"] in ("Trung bình", "Thấp")


def test_no_verified_claims_means_no_llm_call_and_insufficient_data():
    fake = FakeLLM({})
    w = question_window("Doanh thu tháng 9/2026 của game X", TODAY)
    b = write_brief(fake, "Doanh thu tháng 9/2026 của game X", ["Doanh thu"], [], [], [], w)
    assert fake.calls == 0
    assert b["confidence"] == "Chưa đủ dữ liệu" and b["decision"] == "Cần thêm dữ liệu"


def test_unsupported_numbers_helper():
    c = claim("C1", "S1", "revenue at $625 million in Q1 2025", "$625 million", period="Q1 2025")
    assert unsupported_numbers("625 triệu USD quý 1/2025", [c]) == []
    assert unsupported_numbers("tăng 37,6%", [c]) == ["37,6"]
