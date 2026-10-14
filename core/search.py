"""Web search: Tavily if TAVILY_API_KEY is set, otherwise DuckDuckGo (no key needed)."""
from __future__ import annotations

import os

import requests


def search(query: str, max_results: int = 5) -> list[dict]:
    """Return [{url, title, snippet, published}]."""
    key = os.getenv("TAVILY_API_KEY")
    if key:
        try:
            return _tavily(query, max_results, key)
        except Exception:
            pass
    return _ddg(query, max_results)


def _tavily(query: str, n: int, key: str) -> list[dict]:
    r = requests.post(
        "https://api.tavily.com/search",
        headers={"Authorization": f"Bearer {key}"},
        json={"query": query, "max_results": n, "search_depth": "basic"},
        timeout=30,
    )
    r.raise_for_status()
    return [
        {"url": x["url"], "title": x.get("title", ""), "snippet": x.get("content", ""),
         "published": x.get("published_date")}
        for x in r.json().get("results", [])
    ]


def _ddg(query: str, n: int) -> list[dict]:
    from ddgs import DDGS
    out = []
    for x in DDGS().text(query, max_results=n):
        out.append({"url": x.get("href", ""), "title": x.get("title", ""), "snippet": x.get("body", ""),
                    "published": None})
    return out


def search_engine_name() -> str:
    return "Tavily" if os.getenv("TAVILY_API_KEY") else "DuckDuckGo"
