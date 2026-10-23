"""Render the Streamlit page with a finished offline run and check the Mission 3 sections show up."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from tests.test_m3 import FollowLLM, _first_run

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_result_page_shows_trusted_uncertain_and_next_steps():
    r = _first_run(FollowLLM())
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["result"] = r
    at.session_state["plan"] = r["plan"]
    at.run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    for heading in ("Kết luận", "Nên làm gì tiếp", "Dựa trên bằng chứng nào", "Có thể tin", "Chưa chắc chắn",
                    "Nên tìm hiểu tiếp ở đâu"):
        assert heading in text
    # Change Request A4: the decision card comes before the long report
    assert text.index("Nên làm gì tiếp") < text.index("Dựa trên bằng chứng nào") < text.index("Nên tìm hiểu tiếp ở đâu")
    assert at.text_input[0].label.startswith("Hỏi tiếp")


def test_text_from_sources_is_escaped_before_it_reaches_the_page():
    """Quotes and claims come from web pages and the LLM; they must not inject HTML into the page."""
    r = _first_run(FollowLLM())
    r["brief"]["summary"] = '<img src=x onerror="alert(1)">'
    if "card" in r["brief"]:
        r["brief"]["card"]["action"] = '<script>alert("evil action")</script>'
        if r["brief"]["card"]["evidence"]:
            r["brief"]["card"]["evidence"][0]["label"] = '<b id="evil">evil label</b>'
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["result"] = r
    at.session_state["plan"] = r["plan"]
    at.run()
    text = " ".join(m.value for m in at.markdown)
    assert "<img src=x" not in text and "&lt;img src=x" in text
    assert "<script>" not in text and "&lt;script&gt;" in text
    assert '<b id="evil">' not in text and '&lt;b id=&quot;evil&quot;&gt;' in text


def test_stored_live_runs_open_from_the_sidebar_without_an_llm():
    """A grader opening the demo with no history and no quota can still see real results."""
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    at.button(key="eTC2").click().run()
    assert not at.exception
    assert at.session_state["result"]["question"].startswith("Quy mô thị trường game Đông Nam Á năm 2024")
    text = " ".join(m.value for m in at.markdown)
    assert "Có thể tin" in text and "Chưa chắc chắn" in text
    # Change Request A4: decision card shows in sample results as well
    assert "Nên làm gì tiếp" in text and "Dựa trên bằng chứng nào" in text
    assert text.index("Nên làm gì tiếp") < text.index("Dựa trên bằng chứng nào") < text.index("Nên tìm hiểu tiếp ở đâu")
