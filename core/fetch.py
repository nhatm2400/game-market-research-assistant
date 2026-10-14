"""Download and read sources: web pages with trafilatura, PDFs with PyMuPDF.

Fetched text is cached on disk (data/cache) so the same source gives the same text when a
question or a test case is run again.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

import requests

from .models import Source
from .sources import domain_of

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")
MAX_PDF_PAGES = 80


def _sid(url: str) -> str:
    return "S" + hashlib.sha1(url.encode()).hexdigest()[:8]


def _clean(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    return re.sub(r"[ \t]+\n", "\n", text)


def pdf_text(data: bytes) -> tuple[str, str]:
    import fitz  # PyMuPDF
    doc = fitz.open(stream=data, filetype="pdf")
    parts = []
    for i, page in enumerate(doc):
        if i >= MAX_PDF_PAGES:
            break
        parts.append(f"\n[[Trang {i + 1}]]\n" + page.get_text())
    title = (doc.metadata or {}).get("title") or ""
    return "".join(parts), title


def _pdf_date(data: bytes) -> str | None:
    import fitz
    meta = fitz.open(stream=data, filetype="pdf").metadata or {}
    m = re.match(r"D:(\d{4})(\d{2})(\d{2})", meta.get("creationDate") or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def fetch(url: str, hint_published: str | None = None, use_cache: bool = True) -> Source:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    sid = _sid(url)
    cache = CACHE_DIR / f"{sid}.json"
    if use_cache and cache.exists():
        return Source(**json.loads(cache.read_text(encoding="utf-8")))

    src = Source(id=sid, url=url, domain=domain_of(url))
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
        r.raise_for_status()
        ctype = r.headers.get("content-type", "").lower()
        if "pdf" in ctype or url.lower().endswith(".pdf"):
            src.kind = "pdf"
            text, title = pdf_text(r.content)
            src.text, src.title = _clean(text), title
            src.published = hint_published or _pdf_date(r.content)
        else:
            import trafilatura
            doc = trafilatura.bare_extraction(r.content, url=url, include_tables=True, with_metadata=True,
                                              favor_recall=True)
            if doc is not None and hasattr(doc, "as_dict"):
                doc = doc.as_dict()
            if doc:
                src.text = _clean(doc.get("text") or "")
                src.title = doc.get("title") or ""
                src.published = doc.get("date") or hint_published
        if len(src.text) < 200:
            src.error = "Trang không có nội dung đọc được (có thể bị chặn hoặc chỉ có ảnh)"
    except Exception as e:
        src.error = f"Không tải được: {e.__class__.__name__}"
    if not src.error:
        cache.write_text(json.dumps(src.to_dict(with_text=True), ensure_ascii=False), encoding="utf-8")
    return src


def from_upload(name: str, data: bytes, published: str | None = None) -> Source:
    sid = "U" + hashlib.sha1(data).hexdigest()[:8]
    src = Source(id=sid, url=f"upload://{name}", title=name, kind="upload", domain="tải lên",
                 published=published or date.today().isoformat())
    if name.lower().endswith(".pdf"):
        text, title = pdf_text(data)
        src.text, src.title = _clean(text), title or name
    else:
        src.text = _clean(data.decode("utf-8", errors="replace"))
    if len(src.text) < 200:
        src.error = "File không có chữ đọc được (có thể là PDF dạng ảnh)"
    return src
