"""Thin LLM wrapper. Default is Gemini (free tier); any OpenAI-compatible API such as Groq
also works. Every call returns parsed JSON.

Overloaded or rate-limited models are retried with a short back-off. If a model keeps
failing, the call moves on to the next model in the fallback list (LLM_FALLBACK_MODELS).
"""
from __future__ import annotations

import json
import os
import re
import time

ATTEMPTS_PER_MODEL = 3
LONG_WAIT_SECONDS = 90      # a 429 asking for a longer wait than this means the quota is used up
FATAL = ("API_KEY_INVALID", "API key not valid", "PERMISSION_DENIED", "UNAUTHENTICATED", "401", "403")
NEXT_MODEL = ("NOT_FOUND", "404", "UNAVAILABLE", "503", "overloaded", "high demand")
DEFAULT_GEMINI_FALLBACKS = "gemini-2.5-flash,gemini-2.5-flash-lite"


class LLMError(RuntimeError):
    pass


def classify(msg: str) -> str:
    """'fatal' stops at once, 'exhausted' means the quota of this model is used up for now,
    'retry' is transient."""
    if any(s in msg for s in FATAL):
        return "fatal"
    if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
        if "PerDay" in msg or "per day" in msg.lower() or retry_seconds(msg) > LONG_WAIT_SECONDS:
            return "exhausted"
    return "retry"


def retry_seconds(msg: str) -> float:
    """Seconds the API asks us to wait: 'retry in 20h50m53.4s', 'retry in 12.5s', "retryDelay': '75053s'"."""
    m = re.search(r"retry in ((?:\d+(?:\.\d+)?[hms])+)", msg) or re.search(r"retryDelay['\"]?: ?['\"]?((?:\d+(?:\.\d+)?[hms])+)", msg)
    if not m:
        return 0.0
    total = 0.0
    for num, unit in re.findall(r"(\d+(?:\.\d+)?)([hms])", m.group(1)):
        total += float(num) * {"h": 3600, "m": 60, "s": 1}[unit]
    return total


class LLM:
    def __init__(self, provider: str | None = None, model: str | None = None):
        self.provider = (provider or os.getenv("LLM_PROVIDER") or "gemini").lower()
        self.calls = 0
        fallbacks = os.getenv("LLM_FALLBACK_MODELS")
        if self.provider == "gemini":
            key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not key:
                raise LLMError("Thiếu GEMINI_API_KEY (xem .env.example)")
            from google import genai
            self._client = genai.Client(api_key=key)
            self.model = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
            fallbacks = DEFAULT_GEMINI_FALLBACKS if fallbacks is None else fallbacks
        else:
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise LLMError("Thiếu OPENAI_API_KEY cho nhà cung cấp tương thích OpenAI")
            from openai import OpenAI
            self._client = OpenAI(api_key=key, base_url=os.getenv("OPENAI_BASE_URL") or None)
            self.model = model or os.getenv("LLM_MODEL") or "llama-3.3-70b-versatile"
            fallbacks = fallbacks or ""
        self.models = [self.model] + [m.strip() for m in fallbacks.split(",")
                                      if m.strip() and m.strip() != self.model]
        self.models_used: set[str] = set()
        self.exhausted: dict[str, float] = {}      # model -> time (epoch seconds) when its quota resets

    def json(self, prompt: str, schema: dict) -> dict:
        last = None
        for model in self.models:
            if self._is_exhausted(model):
                continue
            for attempt in range(ATTEMPTS_PER_MODEL):
                try:
                    self.calls += 1
                    out = _parse_json(self._call(model, prompt, schema))
                    self.models_used.add(model)
                    return out
                except Exception as e:
                    last = e
                    msg = str(e)
                    kind = classify(msg)
                    if kind == "fatal":
                        raise LLMError(f"Gọi LLM thất bại: {msg[:300]}") from e
                    if kind == "exhausted":
                        self.exhausted[model] = time.time() + retry_seconds(msg)
                        break                      # no point waiting: use the next model
                    unavailable = any(s in msg for s in NEXT_MODEL)
                    if unavailable and (attempt >= 1 or "NOT_FOUND" in msg or "404" in msg):
                        break                      # overloaded twice or no such model: try the next one
                    if attempt < ATTEMPTS_PER_MODEL - 1:
                        time.sleep(_wait_seconds(msg, attempt))
        if all(self._is_exhausted(m) for m in self.models):
            wait = max(0.0, min(self.exhausted[m] for m in self.models) - time.time()) / 3600
            raise LLMError("Đã hết hạn mức miễn phí trong ngày của " + ", ".join(self.models)
                           + f". Hạn mức mở lại sau khoảng {wait:.0f} giờ. Có thể đổi LLM_MODEL hoặc dùng khóa API "
                           "của một dự án Google khác trong file .env.")
        raise LLMError(f"Gọi LLM thất bại sau khi thử {', '.join(self.models)}: {str(last)[:300]}")

    def _is_exhausted(self, model: str) -> bool:
        return self.exhausted.get(model, 0) > time.time()

    def _call(self, model: str, prompt: str, schema: dict) -> str:
        if self.provider == "gemini":
            from google.genai import types
            cfg = types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_json_schema=schema,
            )
            resp = self._client.models.generate_content(model=model, contents=prompt, config=cfg)
            return resp.text or ""
        resp = self._client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Reply with one JSON object that follows this JSON schema: "
                 + json.dumps(schema, ensure_ascii=False)},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content or ""


def _wait_seconds(msg: str, attempt: int) -> float:
    delay = retry_seconds(msg)
    return min(delay + 1, 60) if delay else 5 * (attempt + 1)


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
    return json.loads(raw)
