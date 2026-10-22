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
    for heading in ("Có thể tin", "Chưa chắc chắn", "Nên tìm hiểu tiếp ở đâu"):
        assert heading in text
    callouts = [*at.success, *at.warning, *at.info]
    assert any(c.value.startswith(f"**Kết luận: {r['brief']['decision']}**") for c in callouts)
    assert any(m.label == "Có thể tin" for m in at.metric)
    assert at.text_input[0].label.startswith("Hỏi tiếp")
