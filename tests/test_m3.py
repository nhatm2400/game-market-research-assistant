"""Mission 3: what can be trusted, what is still uncertain and where to look next; one-click evidence;
follow-up research that keeps its context; old and forecast figures. No network, no API key."""
from core import pipeline
from core.analyze import build_findings, enrich_claim, stale_forecast_flag
from core.brief import write_brief
from core.evidence import evidence_url, sort_evidence
from core.fetch import from_upload
from core.models import Source
from core.periods import period_flags, question_window
from core.textnorm import parse_value
from core.sources import assess_claim, assess_source
from core.verify import verify_claim
from tests.test_core import NIKO_TEXT, ST_TEXT, STATISTA_TEXT, TODAY, FakeLLM, _verified, claim, src
from tests.test_pipeline_offline import ScriptedLLM

W_Q1 = question_window("Doanh thu IAP game mobile Đông Nam Á quý 1/2025?", TODAY)
ST_Q = "SEA currently ranks seventh globally in in-app purchase (IAP) revenue at $625 million in Q1 2025"
RELAY_TEXT = "Sensor Tower data shows Southeast Asian users spent $625 million on games in Q1 2025, up 1% QoQ."
RELAY_Q = "Southeast Asian users spent $625 million on games in Q1 2025, up 1% QoQ"
VN_TEXT = "Newzoo country table: Vietnam games market revenue was $0.82 billion in 2024, up 5% year on year. "
SEA_Q = "Quy mô thị trường game Đông Nam Á năm 2024?"


def _q1(cid, s, quote):
    c = claim(cid, s.id, quote, "$625 million", scope="mobile_iap", period="Q1 2025")
    verify_claim(c, s)
    assess_claim(c, s)
    return enrich_claim(c, W_Q1, "Đông Nam Á", TODAY, s.published)


def _ev(cs, sources, window=W_Q1):
    by_id = {s.id: s for s in sources}
    fs = build_findings(cs, by_id, TODAY)
    return fs, sort_evidence(fs, cs, by_id, window, "Đông Nam Á", [])


def _st():
    return assess_source(src("S1", "https://sensortower.com/blog/x", ST_TEXT, "2025-05-20"), TODAY)


# ---- trusted / uncertain / next steps ----

def test_number_published_by_the_data_firm_itself_can_be_trusted():
    st = _st()
    _, ev = _ev([_q1("C1", st, ST_Q)], [st])
    assert [x["finding"] for x in ev["trusted"]] == ["F1"] and not ev["uncertain"]


def test_relayed_number_from_a_reputable_site_is_trusted_with_a_note_and_a_check_step():
    s = assess_source(src("S2", "https://gamedevreports.substack.com/p/x", RELAY_TEXT, "2025-06-13"), TODAY)
    _, ev = _ev([_q1("C2", s, RELAY_Q)], [s])
    t = ev["trusted"][0]
    assert any("dẫn lại" in n for n in t["notes"])
    assert ev["next_steps"][0]["query"].startswith("Sensor Tower") and ev["next_steps"][0]["findings"] == ["F1"]


def test_relayed_number_from_a_blog_is_uncertain():
    s = assess_source(src("S2", "https://allcorrectgames.com/x", RELAY_TEXT, "2025-06-13"), TODAY)
    _, ev = _ev([_q1("C2", s, RELAY_Q)], [s])
    assert "Chỉ có nguồn hạng C hoặc D" in ev["uncertain"][0]["why"]


def test_figures_for_another_period_are_kept_aside_not_mixed_in():
    """Asked about 2024: the 2025 figure and the 2029 forecast are listed apart, not as uncertain answers."""
    text = "Niko Partners: Southeast Asia games revenue was $5.37 billion in 2024, $5.47 billion in 2025 and $6.47 billion in 2029."
    q = "Southeast Asia games revenue was $5.37 billion in 2024, $5.47 billion in 2025 and $6.47 billion in 2029"
    s = assess_source(src("S5", "https://nikopartners.com/x", text, "2025-09-01"), TODAY)
    cs = [_verified("C1", s, q, "$5.37 billion"), _verified("C2", s, q, "$5.47 billion", period="2025"),
          _verified("C3", s, q, "$6.47 billion", period="2029")]
    fs, ev = _ev(cs, [s], question_window("Quy mô thị trường game Đông Nam Á năm 2024", TODAY))
    assert [x["values"] for x in ev["trusted"]] == ["5,37 tỷ USD"]
    assert len(ev["other"]) == 2 and not ev["uncertain"]


def test_conflict_is_uncertain_and_suggests_comparing_methods():
    niko = assess_source(src("S3", "https://gamesbeat.com/niko", NIKO_TEXT, "2025-09-30"), TODAY)
    sta = assess_source(src("S4", "https://statista.com/x", STATISTA_TEXT, "2025-02-10"), TODAY)
    cs = [_verified("C1", niko, "the Southeast Asia games market generated $5.37 billion in revenue in 2024", "$5.37 billion"),
          _verified("C2", sta, "revenue in the SEA-6 games market amounted to $5.89 billion in 2024", "$5.89 billion")]
    w = question_window("Quy mô thị trường game Đông Nam Á năm 2024", TODAY)
    fs, ev = _ev(cs, [niko, sta], w)
    u = ev["uncertain"][0]
    assert "lệch nhau 10%" in u["why"][0] and "methodology" in u["next_steps"][0]["query"]
    # the spread is computed by code, so the brief may repeat it (M3 TC2 lost its summary over "21%")
    fake = FakeLLM({"decision": "Đã có câu trả lời", "summary": "Từ 5,37 đến 5,89 tỷ USD, các nguồn lệch nhau 10%.",
                    "reasons": [], "what_would_change": []})
    b = write_brief(fake, "Quy mô thị trường game Đông Nam Á năm 2024", ["Quy mô"], cs, fs, [], w,
                    {niko.id: niko, sta.id: sta}, "Đông Nam Á")
    assert b["summary"].endswith("lệch nhau 10%.")


def test_opposite_directions_are_called_out():
    a = assess_source(src("S7", "https://sensortower.com/a", "MOBA revenue in Southeast Asia grew 12% in Q1 2025.",
                          "2025-05-01"), TODAY)
    b = assess_source(src("S8", "https://appmagic.rocks/b", "MOBA revenue in Southeast Asia fell -8% in Q1 2025.",
                          "2025-05-02"), TODAY)
    kw = dict(metric="growth", period="Q1 2025", genre="MOBA", scope="mobile")
    cs = [_verified("C1", a, "MOBA revenue in Southeast Asia grew 12% in Q1 2025", "12%", **kw),
          _verified("C2", b, "MOBA revenue in Southeast Asia fell -8% in Q1 2025", "-8%", **kw)]
    f = build_findings(cs, {a.id: a, b.id: b}, TODAY)[0]
    assert f.status == "conflict" and "trái chiều" in f.reasons[0]


def test_figure_for_a_period_after_publication_is_a_forecast():
    assert stale_forecast_flag("2025", "2024-06-10", TODAY)
    assert "chưa kết thúc" in stale_forecast_flag("2025", "2025-09-30", TODAY)[0]     # Niko's "2025: $5.47 billion"
    assert not stale_forecast_flag("2024", "2025-05-01", TODAY)
    assert not stale_forecast_flag("Q1 2025 vs Q4 2024", "2025-05-21", TODAY)
    assert not stale_forecast_flag("2028", "2024-06-10", TODAY)      # still in the future: period_flags says so


def test_period_running_into_the_future_is_partly_a_forecast():
    w = question_window("Quy mô thị trường game Đông Nam Á năm 2024", TODAY)
    assert any("một phần là số dự báo" in f for f in period_flags("2024-2029", w, TODAY))
    assert not any("dự báo" in f for f in period_flags("2025", w, TODAY))


def test_decimal_with_leading_zero_is_not_read_as_thousands():
    """M2 read the Newzoo table cell '0.817' (billion USD) as 817."""
    assert parse_value("0.817")[0] == 0.817 and parse_value("0,894")[0] == 0.894
    assert parse_value("1.234.567")[0] == 1234567 and parse_value("1,371,171")[0] == 1371171


def test_other_market_is_kept_aside_and_asks_for_the_right_market():
    s = assess_source(src("S2", "https://gamedevreports.substack.com/p/x", RELAY_TEXT, "2025-06-13"), TODAY)
    c = claim("C1", s.id, RELAY_Q, "$625 million", scope="mobile_iap", period="Q1 2025")
    verify_claim(c, s)
    assess_claim(c, s)
    enrich_claim(c, W_Q1, "Việt Nam", TODAY, s.published)
    fs = build_findings([c], {s.id: s}, TODAY)
    ev = sort_evidence(fs, [c], {s.id: s}, W_Q1, "Việt Nam", [])
    assert not ev["trusted"] and not ev["uncertain"] and "câu hỏi hỏi về Việt Nam" in ev["other"][0]["why"][0]
    assert ev["next_steps"][0]["query"].startswith("Vietnam")


def test_older_period_points_to_the_newer_figure():
    text = "Newzoo: the Southeast Asia games market reached $5.1 billion in 2023 and $5.5 billion in 2024."
    q = "the Southeast Asia games market reached $5.1 billion in 2023 and $5.5 billion in 2024"
    s = assess_source(src("S6", "https://newzoo.com/x", text, "2025-08-01"), TODAY)
    cs = [_verified("C1", s, q, "$5.1 billion", period="2023"), _verified("C2", s, q, "$5.5 billion", period="2024")]
    fs, ev = _ev(cs, [s], question_window("Quy mô thị trường game Đông Nam Á", TODAY))
    assert fs[0].newer == fs[1].key
    old = next(x for x in ev["other"] if x["finding"] == fs[0].key)
    assert "số mới hơn" in old["why"][0]
    assert [x["finding"] for x in ev["trusted"]] == [fs[1].key]


def test_bare_numbers_from_a_chart_point_to_the_page():
    text = "[[Trang 5]]\nIntro.\n[[Trang 6]]\nSoutheast Asia Top Subgenre by IAP Revenue\n+17.6%+20.1%-17.1%+37.6%\n"
    s = assess_source(Source(id="S9", url="https://investgame.net/r.pdf", kind="pdf", text=text,
                             published="2025-06-19"), TODAY)
    cs = [claim(f"C{i}", "S9", v, v, metric="growth", period="Q1 2025") for i, v in enumerate(["+17.6%", "+20.1%", "-17.1%"], 1)]
    for c in cs:
        verify_claim(c, s)
    assert all(not c.verified and c.page == 6 for c in cs)
    step = sort_evidence([], cs, {s.id: s}, W_Q1, "Đông Nam Á", [])["next_steps"][0]
    assert step["url"].endswith("#page=6") and "3 con số" in step["text"]
    s.kind, s.url = "html", "https://investgame.net/news/r/"        # same chart on a web page: jump to the first number
    step = sort_evidence([], cs, {s.id: s}, W_Q1, "Đông Nam Á", [])["next_steps"][0]
    assert step["url"] == "https://investgame.net/news/r/#:~:text=%2B17.6%25"


def test_table_labels_before_a_number_are_not_minus_signs():
    """M3 TC2: the cell "S-5.89 N-6.51" (S = Statista, N = Newzoo) became -6,51 tỷ USD and a fake
    "one source says up, another says down" conflict."""
    assert parse_value("N-6.51 billion USD") == (6.51e9, "USD") and parse_value("S-5.89")[0] == 5.89
    assert parse_value("year-on-year growth of 5%")[0] == 5
    assert parse_value("-17.1% QoQ")[0] == -17.1 and parse_value("−3%")[0] == -3 and parse_value("-$2 million")[0] == -2e6


def test_value_with_two_numbers_is_rejected():
    text = "| Total revenue | S-5.35 N-6.17 | S-5.89 N-6.51 | S-6.39 N-6.89 |"
    s = assess_source(src("S4", "https://allcorrectgames.com/x", text * 20, "2026-05-05"), TODAY)
    c = claim("C1", s.id, "| Total revenue | S-5.35 N-6.17 | S-5.89 N-6.51 |", "S-5.89 N-6.51 billion USD")
    verify_claim(c, s)
    assert not c.verified and "nhiều con số" in c.verify_note


def test_label_stitched_to_a_chart_number_is_rejected_but_points_to_the_chart():
    """M3 TC6: the AI paired Battle Royale with +37.6% by stitching words that are not next to each other."""
    text = "[[Trang 6]]\nShooter | Battle Royale\nRPG | Squad RPG\n$0M $50M $100M\n+17.6%+20.1%-17.1%-11.7%-5.1%+37.6%\n"
    s = assess_source(Source(id="S9", url="https://investgame.net/r.pdf", kind="pdf", text=text, published="2025-06-19"), TODAY)
    cs = [claim(f"C{i}", "S9", f"Shooter | Battle Royale | $0M | {v}", v, metric="growth", period="Q1 2025")
          for i, v in enumerate(["+37.6%", "+17.6%", "+20.1%"], 1)]
    for c in cs:
        verify_claim(c, s)
    assert all(not c.verified and "con số có trong nguồn" in c.verify_note and c.page == 6 for c in cs)
    step = sort_evidence([], cs, {s.id: s}, W_Q1, "Đông Nam Á", [])["next_steps"][0]
    assert step["url"].endswith("#page=6") and "nhãn bị ghép với số" in step["text"]


def test_revenue_without_currency_is_compared_as_usd():
    """M3 TC2: a copy of Niko's figure written "5.37 billion" was not compared with "$5.89 billion"."""
    s = assess_source(src("S3", "https://gamesbeat.com/niko", NIKO_TEXT.replace("$5.37", "5.37"), "2025-09-30"), TODAY)
    c = _verified("C1", s, "the Southeast Asia games market generated 5.37 billion in revenue in 2024", "5.37 billion")
    assert c.unit == "USD" and any("coi là USD" in f for f in c.flags)


def test_evidence_link_opens_the_quote():
    u = evidence_url("https://a.com/p#top", "html", "Revenue in the SEA-6 games market amounted to $5.89 billion in 2024", None)
    assert u == "https://a.com/p#:~:text=Revenue%20in%20the%20SEA%2D6%20games,to%20%245.89%20billion%20in%202024"
    assert evidence_url("https://a.com/r.pdf", "pdf", "x", 6) == "https://a.com/r.pdf#page=6"
    assert evidence_url("upload://f.pdf", "upload", "x", 2) == ""


# ---- brief: regression of M2 bugs ----

def test_numbers_from_the_question_are_allowed_and_lookup_questions_get_an_answer():
    """TC3 in M2 lost its summary because '12 tháng' was taken for an invented number; TC1 got
    'Cần thêm dữ liệu' although the number was found."""
    st = _st()
    c = _q1("C1", st, ST_Q)
    fs = build_findings([c], {st.id: st}, TODAY)
    q = "Doanh thu IAP game mobile Đông Nam Á trong 12 tháng qua là bao nhiêu?"
    fake = FakeLLM({"decision": "Đã có câu trả lời",
                    "summary": "Trong 12 tháng qua chỉ có số quý 1/2025: 625 triệu USD.",
                    "reasons": [{"text": "Doanh thu IAP quý 1/2025 là 625 triệu USD.", "claim_ids": ["C1"]}],
                    "what_would_change": []})
    b = write_brief(fake, q, ["Doanh thu"], [c], fs, [], question_window(q, TODAY), {st.id: st}, "Đông Nam Á")
    assert b["summary"].startswith("Trong 12 tháng qua")
    assert b["decision"] == "Đã có câu trả lời"
    assert b["reasons"][0]["status"] == "trusted" and b["trusted"]


def test_answer_resting_only_on_uncertain_findings_is_not_presented_as_settled():
    """M3 TC8: the only 2025 figure was a forecast, yet the brief said 'Đã có câu trả lời'."""
    s = assess_source(src("S2", "https://allcorrectgames.com/x", RELAY_TEXT, "2025-06-13"), TODAY)
    c = _q1("C2", s, RELAY_Q)
    fs = build_findings([c], {s.id: s}, TODAY)
    reason = {"text": "Doanh thu IAP quý 1/2025 là 625 triệu USD.", "claim_ids": ["C2"]}
    for asked, expected in [("Đã có câu trả lời", "Có số liệu nhưng chưa chắc chắn"), ("Nên ưu tiên", "Cần thêm dữ liệu")]:
        fake = FakeLLM({"decision": asked, "summary": "", "reasons": [reason], "what_would_change": []})
        b = write_brief(fake, "Doanh thu IAP game mobile Đông Nam Á quý 1/2025?", ["Doanh thu"], [c], fs, [], W_Q1,
                        {s.id: s}, "Đông Nam Á")
        assert b["reasons"][0]["status"] == "uncertain" and b["decision"] == expected
        assert any("không lý do nào dựa trên nhận định có thể tin" in x for x in b["guard_log"])


# ---- follow-up research ----

class FollowLLM(ScriptedLLM):
    def json(self, prompt, schema):
        props = schema["properties"]
        if "standalone_question" in props:
            self.calls += 1
            return {"standalone_question": "Quy mô thị trường game Việt Nam năm 2024 là bao nhiêu?",
                    "criteria": ["Quy mô thị trường"], "queries": [], "market": "Việt Nam", "genre": ""}
        if "claims" in props and "Vietnam games market" in prompt:
            self.calls += 1
            return {"claims": [{"claim_text": "Thị trường game Việt Nam năm 2024 đạt 0,82 tỷ USD.", "metric": "revenue",
                                "value_text": "$0.82 billion", "market": "Vietnam", "period": "2024",
                                "scope": "all_games", "genre": "", "genre_level": "all",
                                "quote": "Vietnam games market revenue was $0.82 billion in 2024",
                                "section_title": "", "attributed_to": "Newzoo", "criterion": 0}]}
        return super().json(prompt, schema)


def _first_run(llm):
    ups = [from_upload("niko.txt", (NIKO_TEXT * 3).encode()), from_upload("statista.txt", (STATISTA_TEXT * 4).encode()),
           from_upload("vn.txt", (VN_TEXT * 4).encode())]
    return pipeline.run(SEA_Q, uploads=ups, use_search=False, llm=llm, today=TODAY)


def test_follow_up_keeps_context_and_switches_only_what_was_asked():
    llm = FollowLLM()
    prev = _first_run(llm)
    for c in prev["claims"]:
        c["excluded_by_user"] = c["value_text"] == "$5.89 billion"      # the user dropped the Statista figure
    res = pipeline.follow_up(prev, "Còn Việt Nam thì sao?", use_search=False, llm=llm, today=TODAY)

    assert res["question"] == "Quy mô thị trường game Việt Nam năm 2024 là bao nhiêu?"
    assert res["question_market"] == "Việt Nam" and res["window"]["label"] == "01/2024 đến 12/2024"
    assert {c["id"] for c in prev["claims"]} <= {c["id"] for c in res["claims"]}
    assert res["stats"]["carried"] == prev["stats"]["verified"] == 3
    assert res["stats"]["llm_calls"] == 2            # plan + brief: pages already read are not read again
    by_val = {c["value_text"]: c for c in res["claims"]}
    assert by_val["$5.89 billion"]["excluded_by_user"]
    assert not any("câu hỏi hỏi về" in f for f in by_val["$0.82 billion"]["flags"])
    assert any("câu hỏi hỏi về Việt Nam" in f for f in by_val["$5.37 billion"]["flags"])
    assert [t["question"] for t in res["thread"]] == [SEA_Q, res["question"]] and res["parent_id"] == prev["id"]


def test_next_step_search_skips_pages_already_read(monkeypatch):
    llm = FollowLLM()
    prev = _first_run(llm)
    monkeypatch.setattr(pipeline, "search", lambda q, n: [{"url": prev["sources"][0]["url"], "title": "", "published": None}])
    res = pipeline.follow_up(prev, queries=["Niko Partners Southeast Asia games market 2024"], llm=llm, today=TODAY)
    assert any("lần nghiên cứu trước" in x["reason"] for x in res["skipped"])
    assert res["question"] == SEA_Q and res["stats"]["llm_calls"] == 1      # brief only


def test_llm_calls_are_counted_per_run():
    llm = FollowLLM()
    a, b = _first_run(llm), _first_run(llm)
    assert a["stats"]["llm_calls"] == b["stats"]["llm_calls"] > 0


def test_value_must_agree_with_the_quote_in_sign_scale_and_unit():
    """Same digits are not enough: a flipped sign makes a fake conflict, a wrong scale or pairing a wrong number."""
    quote = "The Southeast Asia games market grew 8% to $6.2 billion in 2024, according to the report."
    s = assess_source(src("S1", "https://nikopartners.com/x", quote * 5, "2025-03-01"), TODAY)
    for value, why in [("-8%", "dấu"), ("$6.2 trillion", "bậc"), ("$8 billion", "đơn vị")]:
        c = claim("C1", s.id, quote, value)
        verify_claim(c, s)
        assert not c.verified and why in c.verify_note, value
    for value in ["8%", "$6.2 billion", "6,2 tỷ USD"]:
        c = claim("C1", s.id, quote, value)
        verify_claim(c, s)
        assert c.verified, value


def test_value_check_keeps_declines_and_table_cells_without_a_scale_word():
    from core.textnorm import value_mismatch
    assert value_mismatch("-17.1%", "MOBA revenue declined 17.1% quarter on quarter") == ""
    assert value_mismatch("-17.1%", "+20.1%-17.1%-11.7%") == ""
    assert value_mismatch("$5.37 billion", "Revenue (USD bn) | 5.37 | 5.89") == ""
    assert value_mismatch("S-5.89", "| Total revenue | S-5.35 N-6.17 | S-5.89 N-6.51 |") == ""


def test_weaker_newer_figure_does_not_push_a_measured_figure_aside():
    """A blog's 2026 figure must not hide Newzoo's 2024 figure for a question without a year."""
    nz = assess_source(src("S6", "https://newzoo.com/x", "Newzoo: the Southeast Asia games market reached $5.5 billion in 2024.",
                           "2025-08-01"), TODAY)
    blog = assess_source(src("S7", "https://some-gaming-blog.net/x",
                             "Our estimate: the Southeast Asia games market will hit $7.2 billion in 2026.", "2026-02-01"), TODAY)
    cs = [_verified("C1", nz, "the Southeast Asia games market reached $5.5 billion in 2024", "$5.5 billion", period="2024"),
          _verified("C2", blog, "the Southeast Asia games market will hit $7.2 billion in 2026", "$7.2 billion", period="2026")]
    fs, ev = _ev(cs, [nz, blog], question_window("Quy mô thị trường game Đông Nam Á", TODAY))
    assert not fs[0].newer
    assert fs[0].key in [x["finding"] for x in ev["trusted"]]


def test_unstated_currency_and_market_are_not_trusted():
    assert parse_value("Rp 30 trillion")[1] == "IDR" and parse_value("S$1.2 billion")[1] == "SGD"
    s = assess_source(src("S1", "https://nikopartners.com/x",
                          "In 2024 the market generated 5.37 billion in revenue. Mobile titles earned $2.1 billion in 2024.",
                          "2025-03-01"), TODAY)
    no_cur = _verified("C1", s, "In 2024 the market generated 5.37 billion in revenue", "5.37 billion")
    no_mkt = _verified("C2", s, "Mobile titles earned $2.1 billion in 2024", "$2.1 billion", market="", scope="mobile")
    fs, ev = _ev([no_cur, no_mkt], [s], question_window("Quy mô thị trường game Đông Nam Á năm 2024", TODAY))
    assert not ev["trusted"]
    why = " ".join(w for x in ev["uncertain"] for w in x["why"])
    assert "coi là USD" in why and "không ghi rõ thị trường" in why


def test_comparison_period_on_a_revenue_figure_does_not_split_it():
    """TC1: the same $625M appeared twice as trusted because one copy had period 'Q1 2025 vs Q4 2024'."""
    s = assess_source(src("S1", "https://sensortower.com/x", ST_TEXT * 3, "2025-05-20"), TODAY)
    q = "SEA currently ranks seventh globally in in-app purchase (IAP) revenue at $625 million in Q1 2025"
    cs = [_verified("C1", s, q, "$625 million", period="Q1 2025", scope="mobile_iap"),
          _verified("C2", s, q, "$625 million", period="Q1 2025 vs Q4 2024", scope="mobile_iap")]
    assert cs[1].period == "Q1 2025"
    assert len(build_findings(cs, {s.id: s}, TODAY)) == 1


def _tc2_like():
    """Niko 5.37 vs Statista 5.89 (conflict, uncertain) and one trusted Newzoo player count."""
    srcs = [assess_source(src("S1", "https://nikopartners.com/x", NIKO_TEXT, "2025-06-01"), TODAY),
            assess_source(src("S2", "https://www.statista.com/x", STATISTA_TEXT, "2025-06-01"), TODAY),
            assess_source(src("S3", "https://newzoo.com/x", "Southeast Asia had 285.82 million gamers in 2024.",
                              "2025-06-01"), TODAY)]
    cs = [_verified("C1", srcs[0], "the Southeast Asia games market generated $5.37 billion in revenue in 2024",
                    "$5.37 billion"),
          _verified("C2", srcs[1], "revenue in the SEA-6 games market amounted to $5.89 billion in 2024", "$5.89 billion"),
          _verified("C3", srcs[2], "Southeast Asia had 285.82 million gamers in 2024", "285.82 million", metric="players")]
    return srcs, cs


def test_settled_answer_needs_most_reasons_to_be_trusted():
    """M3 TC2: one trusted side figure must not make 'Đã có câu trả lời' when the asked market size is in conflict."""
    srcs, cs = _tc2_like()
    w = question_window("Quy mô thị trường game Đông Nam Á năm 2024", TODAY)
    fs = build_findings(cs, {s.id: s for s in srcs}, TODAY)
    reasons = [{"text": "Đông Nam Á có 285,82 triệu người chơi.", "claim_ids": ["C3"]},
               {"text": "Niko Partners ghi 5,37 tỷ USD.", "claim_ids": ["C1"]},
               {"text": "Statista ghi 5,89 tỷ USD.", "claim_ids": ["C2"]}]
    fake = FakeLLM({"decision": "Đã có câu trả lời", "summary": "", "reasons": reasons, "what_would_change": []})
    b = write_brief(fake, "Quy mô thị trường game Đông Nam Á năm 2024?", ["Quy mô"], cs, fs, [], w,
                    {s.id: s for s in srcs}, "Đông Nam Á")
    assert [x["status"] for x in b["reasons"]] == ["trusted", "uncertain", "uncertain"]
    assert b["decision"] == "Có số liệu nhưng chưa chắc chắn"
    assert any("chỉ 1/3 lý do" in x for x in b["guard_log"])


def test_brief_guard_checks_single_digit_figures_but_allows_numbers_code_showed_the_llm():
    srcs, cs = _tc2_like()
    cs.append(_verified("C4", srcs[1], "revenue in the SEA-6 games market amounted to $5.89 billion in 2024", "$5.89 billion"))
    w = question_window("Quy mô thị trường game Đông Nam Á năm 2024", TODAY)
    fs = build_findings(cs, {s.id: s for s in srcs}, TODAY)
    reasons = [{"text": "Thị trường đạt 6 tỷ USD, tăng 9%.", "claim_ids": ["C1"]},
               {"text": "Có 2 nguồn gốc ghi số khác nhau, lệch 10%.", "claim_ids": ["C1", "C2"]}]
    fake = FakeLLM({"decision": "Cần thêm dữ liệu", "summary": "Hai nguồn lệch nhau 10%, gấp 4 lần sai số thường gặp.",
                    "reasons": reasons, "what_would_change": []})
    b = write_brief(fake, "Quy mô thị trường game Đông Nam Á năm 2024?", ["Quy mô"], cs, fs, [], w,
                    {s.id: s for s in srcs}, "Đông Nam Á")
    assert [x["text"] for x in b["reasons"]] == ["Có 2 nguồn gốc ghi số khác nhau, lệch 10%."]
    assert b["summary"] == ""          # "4 lần" is a figure the sources never gave


def test_numbers_formatted_by_code_are_not_treated_as_invented():
    """M3 TC7: the finding line showed the LLM '460 triệu USD' for $0.46 billion, then the guard dropped it."""
    s = assess_source(src("S2", "https://www.statista.com/x", "Vietnam games revenue reached $0.46 billion in 2024.",
                          "2025-06-01"), TODAY)
    c = _verified("C1", s, "Vietnam games revenue reached $0.46 billion in 2024", "$0.46 billion", market="Vietnam")
    w = question_window("Quy mô thị trường game Việt Nam năm 2024", TODAY)
    fs = build_findings([c], {s.id: s}, TODAY)
    fake = FakeLLM({"decision": "Cần thêm dữ liệu", "summary": "Statista ghi 460 triệu USD.",
                    "reasons": [{"text": "Statista ghi 460 triệu USD cho năm 2024.", "claim_ids": ["C1"]}],
                    "what_would_change": []})
    b = write_brief(fake, "Quy mô thị trường game Việt Nam năm 2024?", ["Quy mô"], [c], fs, [], w, {s.id: s}, "Việt Nam")
    assert b["summary"] == "Statista ghi 460 triệu USD." and len(b["reasons"]) == 1
