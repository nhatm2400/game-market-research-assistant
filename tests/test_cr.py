"""Change Request A4 (hỗ trợ quyết định): the user does not read a long report; they want to know what to do
next and which evidence that rests on. The decision card is picked by code from the brief. No network, no API key."""
from core.analyze import build_findings
from core.brief import write_brief
from core.periods import question_window
from core.sources import assess_source
from tests.test_core import NIKO_TEXT, STATISTA_TEXT, TODAY, FakeLLM, _verified, src
from tests.test_m3 import RELAY_Q, RELAY_TEXT, ST_Q, W_Q1, _q1, _st

Q_SIZE = "Quy mô thị trường game Đông Nam Á năm 2024"


def _brief(llm_out, claims, sources, question="Doanh thu IAP game mobile Đông Nam Á quý 1/2025?", window=W_Q1,
           criteria=("Doanh thu",)):
    by_id = {s.id: s for s in sources}
    fs = build_findings(claims, by_id, TODAY)
    return write_brief(FakeLLM(llm_out) if llm_out else None, question, list(criteria), claims, fs, [], window,
                       by_id, "Đông Nam Á")


def test_change_request_answer_with_trusted_evidence_says_use_it_and_links_the_quote():
    st = _st()
    c = _q1("C1", st, ST_Q)
    card = _brief({"decision": "Đã có câu trả lời", "summary": "625 triệu USD.",
                   "reasons": [{"text": "Doanh thu IAP quý 1/2025 là 625 triệu USD.", "claim_ids": ["C1"]}],
                   "what_would_change": []}, [c], [st])["card"]
    assert card["action"].startswith("Có thể dùng")
    ev = card["evidence"][0]
    assert ev["status"] == "trusted" and ev["values"] == "625 triệu USD" and ev["tier"] == "A"
    assert ev["url"].startswith("https://sensortower.com/blog/x#:~:text=")


def test_change_request_conflicting_sources_say_do_not_rely_yet_and_what_to_check():
    niko = assess_source(src("S3", "https://gamesbeat.com/niko", NIKO_TEXT, "2025-09-30"), TODAY)
    sta = assess_source(src("S4", "https://statista.com/x", STATISTA_TEXT, "2025-02-10"), TODAY)
    cs = [_verified("C1", niko, "the Southeast Asia games market generated $5.37 billion in revenue in 2024", "$5.37 billion"),
          _verified("C2", sta, "revenue in the SEA-6 games market amounted to $5.89 billion in 2024", "$5.89 billion")]
    b = _brief({"decision": "Đã có câu trả lời", "summary": "Từ 5,37 đến 5,89 tỷ USD.",
                "reasons": [{"text": "Niko ghi 5,37 tỷ USD, Statista ghi 5,89 tỷ USD.", "claim_ids": ["C1", "C2"]}],
                "what_would_change": []}, cs, [niko, sta], Q_SIZE, question_window(Q_SIZE, TODAY))
    card = b["card"]
    assert b["decision"] == "Có số liệu nhưng chưa chắc chắn" and card["action"].startswith("Chưa nên dùng")
    assert "methodology" in card["next_step"]["query"]
    assert [e["status"] for e in card["evidence"]] == ["uncertain"]
    # each side of the conflict can be opened at its own quote
    links = {x["origin"]: x for x in card["evidence"][0]["links"]}
    assert set(links) == {"Niko Partners", "Statista"}
    assert links["Statista"]["url"].startswith("https://statista.com/x#:~:text=") and links["Statista"]["value"] == "$5.89 billion"


def test_change_request_specific_action_only_when_the_code_lets_the_conclusion_stand():
    """The AI may word the next action for a firm conclusion; once the guard downgrades it, the code's own
    instruction replaces a confident-sounding sentence."""
    st = _st()
    trusted = _q1("C1", st, ST_Q)
    out = {"decision": "Nên ưu tiên", "summary": "", "next_action": "Ưu tiên thị trường này; kiểm thêm chi phí quảng cáo.",
           "reasons": [{"text": "Doanh thu IAP quý 1/2025 là 625 triệu USD.", "claim_ids": ["C1"]}], "what_would_change": []}
    assert _brief(out, [trusted], [st])["card"]["action"] == "Ưu tiên thị trường này; kiểm thêm chi phí quảng cáo."
    s = assess_source(src("S2", "https://allcorrectgames.com/x", RELAY_TEXT, "2025-06-13"), TODAY)
    weak = _q1("C2", s, RELAY_Q)                         # blog only: uncertain, so "Nên ưu tiên" cannot stand
    out["reasons"][0]["claim_ids"] = ["C2"]
    b = _brief(out, [weak], [s])
    assert b["decision"] == "Cần thêm dữ liệu" and b["card"]["action"].startswith("Chưa đủ căn cứ")
    out["next_action"] = "Ưu tiên ngay vì tăng 40%."     # a number from nowhere is dropped like any other
    assert _brief(out, [trusted], [st])["next_action"] == ""


def test_change_request_without_data_says_what_to_collect_and_shows_no_evidence():
    card = _brief(None, [], [], "Doanh thu tháng 9/2026 của game X?", question_window("tháng 9/2026", TODAY),
                  ["Doanh thu tháng 9/2026"])["card"]
    assert card["action"].startswith("Chưa đủ căn cứ") and card["evidence"] == []
    assert card["next_step"]["ask"].endswith("Doanh thu tháng 9/2026")


def test_change_request_card_stays_short_and_never_rests_on_out_of_scope_figures():
    """Five cited findings, one of them about Thailand: the card keeps at most three, all about the question's market."""
    text = ("SEA in-app purchase revenue was $625 million in Q1 2025. SEA downloads reached 1.9 billion in Q1 2025. "
            "SEA MOBA revenue grew 20.1% in Q1 2025. SEA 4X strategy revenue grew 17.6% in Q1 2025. "
            "Thailand leads with $162 million in Q1 2025.")
    st = assess_source(src("S1", "https://sensortower.com/blog/y", text, "2025-05-20"), TODAY)
    specs = [("C1", "SEA in-app purchase revenue was $625 million in Q1 2025", "$625 million", {}),
             ("C2", "SEA downloads reached 1.9 billion in Q1 2025", "1.9 billion", {"metric": "downloads"}),
             ("C3", "SEA MOBA revenue grew 20.1% in Q1 2025", "20.1%", {"metric": "growth", "genre": "MOBA"}),
             ("C4", "SEA 4X strategy revenue grew 17.6% in Q1 2025", "17.6%", {"metric": "growth", "genre": "4X"}),
             ("C5", "Thailand leads with $162 million in Q1 2025", "$162 million", {"market": "Thailand"})]
    cs = []
    for cid, q, v, kw in specs:
        c = _verified(cid, st, q, v, **{"period": "Q1 2025", "scope": "mobile", **kw})
        cs.append(c)
    out = {"decision": "Đã có câu trả lời", "summary": "",
           "reasons": [{"text": f"Lý do {i}.", "claim_ids": [cid]} for i, (cid, *_rest) in enumerate(reversed(specs))],
           "what_would_change": []}
    card = _brief(out, cs, [st])["card"]
    assert len(card["evidence"]) == 3
    assert "C5" not in {e["claim_id"] for e in card["evidence"]}       # Thailand is outside the question
    assert all(e["url"].startswith("https://sensortower.com/blog/y#:~:text=") for e in card["evidence"])
