"""Thin LLM wrapper. Default is Gemini (free tier); any OpenAI-compatible API such as Groq
also works. Every call returns parsed JSON."""
from __future__ import annotations

import json
import os
import re
import time


class LLMError(RuntimeError):
    pass


class LLM:
    def __init__(self, provider: str | None = None, model: str | None = None):
        self.provider = (provider or os.getenv("LLM_PROVIDER") or "gemini").lower()
        self.calls = 0
        if self.provider == "gemini":
            key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not key:
                raise LLMError("Thiếu GEMINI_API_KEY (xem .env.example)")
            from google import genai
            self._client = genai.Client(api_key=key)
            self.model = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        else:
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise LLMError("Thiếu OPENAI_API_KEY cho nhà cung cấp tương thích OpenAI")
            from openai import OpenAI
            self._client = OpenAI(api_key=key, base_url=os.getenv("OPENAI_BASE_URL") or None)
            self.model = model or os.getenv("LLM_MODEL") or "llama-3.3-70b-versatile"

    def json(self, prompt: str, schema: dict, retries: int = 4) -> dict:
        last = None
        for attempt in range(retries):
            try:
                self.calls += 1
                raw = self._call(prompt, schema)
                return _parse_json(raw)
            except Exception as e:  # rate limits and transient errors: back off and retry
                last = e
                msg = str(e)
                if any(s in msg for s in ("API key not valid", "PERMISSION_DENIED", "401")):
                    break
                wait = 8 * (attempt + 1)
                m = re.search(r"retry in ([\d.]+)s", msg) or re.search(r"retryDelay['\"]?: ?['\"]?(\d+)", msg)
                if m:
                    wait = float(m.group(1)) + 1
                time.sleep(min(wait, 60))
        raise LLMError(f"Gọi LLM thất bại: {last}")

    def _call(self, prompt: str, schema: dict) -> str:
        if self.provider == "gemini":
            from google.genai import types
            cfg = types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_json_schema=schema,
            )
            resp = self._client.models.generate_content(model=self.model, contents=prompt, config=cfg)
            return resp.text or ""
        resp = self._client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Reply with one JSON object that follows this JSON schema: "
                 + json.dumps(schema, ensure_ascii=False)},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content or ""


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
    return json.loads(raw)
