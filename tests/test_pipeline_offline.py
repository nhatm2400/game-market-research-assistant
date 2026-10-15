"""Run the whole pipeline with uploaded fixture files and a scripted LLM, so the wiring is
tested without network or API key. The scripted LLM deliberately returns one invented claim."""
from datetime import date

from core import pipeline
from core.fetch import from_upload
from core.report import brief_markdown
from tests.test_core import NIKO_TEXT, ST_TEXT, STATISTA_TEXT

TODAY = date(2026, 10, 13)


class ScriptedLLM:
    provider, model = "fake", "scripted"

    def __init__(self, *args, **kwargs):
        self.calls = 0

    def json(self, prompt, schema):
        self.calls += 1
        props = schema["properties"]
        if "queries" in props:
            return {"criteria": ["Quy mô thị trường", "Tăng trưởng"], "queries": [], "market": "Đông Nam Á", "genre": ""}
        if "claims" in props:
            if "seventh globally" in prompt:
                return {"claims": [
                    _c("Doanh thu IAP game mobile Đông Nam Á quý 1/2025 là 625 triệu USD.", "$625 million", "Q1 2025",
                       "SEA currently ranks seventh globally in in-app purchase (IAP) revenue at $625 million in Q1 2025",
                       scope="mobile_iap"),
                    # invented: this sentence is not in the source
                    _c("Doanh thu game mobile Đông Nam Á tăng 40% năm 2025.", "40%", "2025",
                       "SEA mobile game revenue grew 40% in 2025", metric="growth"),
                ]}
            if "Niko Partners" in prompt:
                return {"claims": [_c("Ngành game SEA-6 năm 2024 đạt 5,37 tỷ USD.", "$5.37 billion", "2024",
                                      "the Southeast Asia games market generated $5.37 billion in revenue in 2024")]}
            if "Statista" in prompt:
                return {"claims": [_c("Thị trường game SEA-6 năm 2024 đạt 5,89 tỷ USD.", "$5.89 billion", "2024",
                                      "revenue in the SEA-6 games market amounted to $5.89 billion in 2024",
                                      attributed_to="Statista")]}
            return {"claims": []}
        return {"decision": "Cần thêm dữ liệu", "summary": "Quy mô năm 2024 nằm trong khoảng 5,37 đến 5,89 tỷ USD.",
                "reasons": [{"text": "Niko Partners ghi 5,37 tỷ USD còn Statista ghi 5,89 tỷ USD.", "claim_ids": ["C3", "C4"]}],
                "what_would_change": ["Có phương pháp đo của hai bên"]}


def _c(text, value, period, quote, metric="revenue", scope="all_games", attributed_to=""):
    return {"claim_text": text, "metric": metric, "value_text": value, "market": "Southeast Asia", "period": period,
            "scope": scope, "genre": "", "genre_level": "all", "quote": quote, "section_title": "",
            "attributed_to": attributed_to, "criterion": 0}


def test_offline_run():
    ups = [from_upload("sensortower.txt", (ST_TEXT * 3).encode()),
           from_upload("niko.txt", (NIKO_TEXT * 3).encode()),
           from_upload("statista.txt", (STATISTA_TEXT * 4).encode())]
    llm = ScriptedLLM()
    r = pipeline.run("Quy mô thị trường game Đông Nam Á năm 2024?", uploads=ups, use_search=False,
                     llm=llm, today=TODAY)
    st = r["stats"]
    assert st["claims"] == 4 and st["verified"] == 3 and st["rejected"] == 1
    rejected = [c for c in r["claims"] if not c["verified"]][0]
    assert "40%" in rejected["value_text"]
    assert len(r["brief"]["conflicts"]) == 1
    assert r["brief"]["gaps"] == ["Tăng trưởng"]
    assert r["brief"]["reasons"]
    md = brief_markdown(r)
    assert "5.37 billion" in md and "Mâu thuẫn" in md
