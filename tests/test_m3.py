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
    _, ev = _ev(cs, [niko, sta], question_window("Quy mô thị trường game Đông Nam Á năm 2024", TODAY))
    u = ev["uncertain"][0]
    assert "lệch" in u["why"][0] and "methodology" in u["next_steps"][0]["query"]


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
