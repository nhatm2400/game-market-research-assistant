"""Retries, model fallback and failure handling (no network)."""
import pytest
import requests

from core import fetch as fetch_mod
from core import llm as llm_mod
from core import pipeline
from core.fetch import from_upload
from core.llm import LLM, LLMError, classify
from tests.test_core import NIKO_TEXT, TODAY
from tests.test_pipeline_offline import ScriptedLLM


def make_llm(models, behaviour):
    obj = object.__new__(LLM)
    obj.provider, obj.calls, obj.models, obj.model, obj.models_used = "gemini", 0, models, models[0], set()
    obj.exhausted = {}
    obj._call = lambda model, prompt, schema: behaviour(model)
    return obj


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(llm_mod.time, "sleep", lambda s: None)
    monkeypatch.setattr(fetch_mod.time, "sleep", lambda s: None)


def test_overloaded_model_falls_back_to_next_model():
    seen = []

    def behaviour(model):
        seen.append(model)
        if model == "big":
            raise RuntimeError("503 UNAVAILABLE. This model is currently experiencing high demand.")
        return '{"ok": true}'

    llm = make_llm(["big", "small"], behaviour)
    assert llm.json("p", {}) == {"ok": True}
    assert seen == ["big", "big", "small"] and llm.models_used == {"small"}


def test_transient_error_is_retried_on_same_model():
    n = {"i": 0}

    def behaviour(model):
        n["i"] += 1
        if n["i"] == 1:
            raise RuntimeError("429 RESOURCE_EXHAUSTED. Please retry in 2s")
        return '{"ok": 1}'

    llm = make_llm(["m"], behaviour)
    assert llm.json("p", {}) == {"ok": 1} and n["i"] == 2


def test_bad_key_fails_at_once():
    def behaviour(model):
        raise RuntimeError("400 INVALID_ARGUMENT. API key not valid. Please pass a valid API key.")

    llm = make_llm(["a", "b"], behaviour)
    with pytest.raises(LLMError):
        llm.json("p", {})
    assert llm.calls == 1


def test_all_models_failing_raises_with_models_listed():
    llm = make_llm(["a", "b"], lambda m: (_ for _ in ()).throw(RuntimeError("503 UNAVAILABLE")))
    with pytest.raises(LLMError, match="a, b"):
        llm.json("p", {})


def test_fetch_retries_timeouts(monkeypatch):
    calls = {"n": 0}

    class Resp:
        status_code = 200
        headers = {"content-type": "text/html"}
        content = b"<html><body>" + b"<p>Revenue was $5.37 billion in 2024 across six countries.</p>" * 10 + b"</body></html>"

        def raise_for_status(self):
            pass

    def fake_get(url, headers=None, timeout=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise requests.ConnectTimeout("timed out")
        return Resp()

    monkeypatch.setattr(fetch_mod.requests, "get", fake_get)
    r = fetch_mod._get("https://example.com/a")
    assert r.status_code == 200 and calls["n"] == 3


def test_fetch_error_message_is_readable(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch_mod, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(fetch_mod.requests, "get",
                        lambda *a, **k: (_ for _ in ()).throw(requests.ConnectTimeout("connect timed out to host x")))
    s = fetch_mod.fetch("https://example.com/b")
    assert s.error and "ConnectTimeout" in s.error and "host x" in s.error


class BriefFailsLLM(ScriptedLLM):
    def json(self, prompt, schema):
        if "decision" in schema["properties"]:
            raise LLMError("Gọi LLM thất bại: 503 UNAVAILABLE")
        return super().json(prompt, schema)


def test_pipeline_keeps_verified_claims_when_the_brief_call_fails():
    ups = [from_upload("niko.txt", (NIKO_TEXT * 3).encode())]
    r = pipeline.run("Quy mô thị trường game Đông Nam Á năm 2024?", uploads=ups, use_search=False,
                     llm=BriefFailsLLM({"niko": ups[0].id}), today=TODAY)
    assert r["stats"]["verified"] == 1
    assert "Không viết được bản tóm tắt" in r["brief"]["summary"]
    assert any("Lỗi khi viết bản tóm tắt" in x for x in r["brief"]["guard_log"])


DAILY = ("429 RESOURCE_EXHAUSTED. You exceeded your current quota. Quota exceeded for metric: "
         "generate_content_free_tier_requests, quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier. "
         "Please retry in 20h50m53.45s.")


def test_retry_seconds_parsing():
    assert llm_mod.retry_seconds("Please retry in 20h50m53.45s.") == pytest.approx(75053.45)
    assert llm_mod.retry_seconds("retry in 12.5s") == 12.5
    assert llm_mod.retry_seconds("'retryDelay': '75053s'") == 75053
    assert llm_mod.retry_seconds("nothing") == 0


def test_daily_quota_skips_to_next_model_without_waiting(monkeypatch):
    slept = []
    monkeypatch.setattr(llm_mod.time, "sleep", lambda s: slept.append(s))
    seen = []

    def behaviour(model):
        seen.append(model)
        if model == "big":
            raise RuntimeError(DAILY)
        return '{"ok": 1}'

    llm = make_llm(["big", "small"], behaviour)
    assert llm.json("p", {}) == {"ok": 1}
    assert llm.json("p", {}) == {"ok": 1}
    assert seen == ["big", "small", "small"] and slept == []      # "big" is not asked again


def test_all_models_out_of_quota_gives_a_clear_message():
    llm = make_llm(["a", "b"], lambda m: (_ for _ in ()).throw(RuntimeError(DAILY)))
    with pytest.raises(LLMError, match="hết hạn mức miễn phí"):
        llm.json("p", {})


def test_technical_failure_is_not_reported_as_missing_data():
    class ExtractFailsLLM(ScriptedLLM):
        def json(self, prompt, schema):
            if "claims" in schema["properties"]:
                raise LLMError("Đã hết hạn mức miễn phí trong ngày")
            return super().json(prompt, schema)

    ups = [from_upload("niko.txt", (NIKO_TEXT * 3).encode())]
    r = pipeline.run("Quy mô thị trường game Đông Nam Á năm 2024?", uploads=ups, use_search=False,
                     llm=ExtractFailsLLM(), today=TODAY)
    assert r["stats"]["sources_failed"] == 1
    assert "lỗi kỹ thuật" in r["brief"]["summary"] and r["brief"]["confidence"] == "Chưa đánh giá"


def test_quota_failure_names_its_cause_and_is_remembered():
    """A per-day 429 without a retry delay used to be forgotten at once, so every call hit the dead model again."""
    assert classify("500 Internal error, request id 40139") == "retry"
    assert classify("403 PERMISSION_DENIED") == "fatal"

    class ExtractFailsLLM(ScriptedLLM):
        def json(self, prompt, schema):
            if "claims" in schema["properties"]:
                raise LLMError("Đã hết hạn mức miễn phí trong ngày")
            return super().json(prompt, schema)

    r = pipeline.run("Quy mô thị trường game Đông Nam Á năm 2024?", uploads=[from_upload("niko.txt", (NIKO_TEXT * 3).encode())],
                     use_search=False, llm=ExtractFailsLLM(), today=TODAY)
    assert "hạn mức" in r["brief"]["summary"] and r["stats"]["llm_error"]


def test_daily_limit_without_retry_delay_is_remembered(monkeypatch):
    llm = LLM.__new__(LLM)
    llm.provider, llm.model, llm.models, llm.calls, llm.models_used, llm.exhausted = "gemini", "m1", ["m1"], 0, set(), {}
    calls = []

    def call(model, prompt, schema):
        calls.append(model)
        raise RuntimeError("429 RESOURCE_EXHAUSTED. Quota exceeded for metric: GenerateRequestsPerDayPerProjectPerModel")
    monkeypatch.setattr(llm, "_call", call)
    for _ in range(2):
        with pytest.raises(LLMError, match="hạn mức"):
            llm.json("x", {"properties": {}})
    assert calls == ["m1"]          # the second request does not hit the exhausted model again
