"""LLM steps: plan the question and pull atomic claims out of a source."""
from __future__ import annotations

import re
from datetime import date

from .llm import LLM
from .models import Claim, Source

CHUNK_CHARS = 12000
MAX_CHUNKS_PER_SOURCE = 3

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "criteria": {"type": "array", "items": {"type": "string"}},
        "queries": {"type": "array", "items": {"type": "string"}},
        "market": {"type": "string"},
        "genre": {"type": "string"},
    },
    "required": ["criteria", "queries", "market", "genre"],
}

PLAN_PROMPT = """Bạn hỗ trợ chuyên viên phát triển kinh doanh của một nhà phát hành game ở Việt Nam nghiên cứu thị trường.
Hôm nay là {today}. Câu hỏi của người dùng:
"{question}"

Hãy lập kế hoạch nghiên cứu:
- criteria: 3 đến 4 tiêu chí đo được để trả lời câu hỏi, viết tiếng Việt, ngắn gọn
  (ví dụ: "Quy mô doanh thu", "Tốc độ tăng trưởng doanh thu", "Mức cạnh tranh trong nhóm doanh thu cao").
- queries: 4 truy vấn tìm kiếm web để tìm số liệu cho các tiêu chí. Viết bằng tiếng Anh vì báo cáo
  thị trường game chủ yếu bằng tiếng Anh; nếu câu hỏi về Việt Nam thì thêm 1 truy vấn tiếng Việt.
  Ưu tiên truy vấn dẫn tới báo cáo của hãng dữ liệu (Sensor Tower, Newzoo, Niko Partners, data.ai, AppMagic).
- market: thị trường câu hỏi nhắm tới (ví dụ "Đông Nam Á", "Việt Nam", "Indonesia"); để trống nếu không rõ.
- genre: thể loại game câu hỏi nhắm tới; để trống nếu câu hỏi không giới hạn thể loại.
Không trả lời câu hỏi, chỉ lập kế hoạch."""

CLAIM_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_text": {"type": "string"},
                    "metric": {"type": "string", "enum": ["revenue", "growth", "downloads", "players", "share", "rank", "other"]},
                    "value_text": {"type": "string"},
                    "market": {"type": "string"},
                    "period": {"type": "string"},
                    "scope": {"type": "string", "enum": ["all_games", "mobile", "mobile_iap", "pc_console", "unknown"]},
                    "genre": {"type": "string"},
                    "genre_level": {"type": "string", "enum": ["all", "genre", "subgenre"]},
                    "quote": {"type": "string"},
                    "section_title": {"type": "string"},
                    "attributed_to": {"type": "string"},
                    "criterion": {"type": "integer"},
                },
                "required": ["claim_text", "metric", "value_text", "market", "period", "scope", "genre",
                             "genre_level", "quote", "section_title", "attributed_to", "criterion"],
            },
        }
    },
    "required": ["claims"],
}

EXTRACT_PROMPT = """Bạn trích số liệu từ một tài liệu để phục vụ nghiên cứu thị trường game.
Câu hỏi nghiên cứu: "{question}"
Các tiêu chí (đánh số từ 0): {criteria}

Tài liệu: "{title}" ({url}), đăng ngày {published}.
--- BẮT ĐẦU NỘI DUNG ---
{text}
--- HẾT NỘI DUNG ---

Hãy liệt kê tối đa 12 nhận định định lượng liên quan đến câu hỏi hoặc các tiêu chí. Quy tắc bắt buộc:
1. quote: chép NGUYÊN VĂN một câu hoặc một dòng bảng trong tài liệu chứa con số, không sửa chữ, không dịch,
   không rút gọn, không ghép hai câu xa nhau. Câu trích phải đủ ý để người đọc hiểu số đó đo cái gì.
2. value_text: con số đúng như cách viết trong quote (ví dụ "$625 million", "37.6%", "5,37 tỷ USD").
   Không đổi đơn vị, không làm tròn, không tự tính.
3. Chỉ dùng thông tin có trong tài liệu. Không dùng kiến thức có sẵn. Nếu tài liệu không có số liệu liên quan,
   trả về danh sách rỗng.
4. claim_text: một câu tiếng Việt diễn đạt nhận định, đủ chỉ số, thị trường, kỳ đo.
5. metric: revenue (doanh thu, quy mô), growth (tỷ lệ tăng trưởng), downloads, players, share (thị phần),
   rank, other. scope: all_games (cả ngành game), mobile (game mobile, tổng), mobile_iap (chỉ mua trong ứng dụng),
   pc_console, unknown.
6. market: thị trường mà CHÍNH BẢNG HOẶC ĐOẠN chứa câu trích nói tới, không phải tên chung của báo cáo.
   Ví dụ báo cáo về Đông Nam Á nhưng bảng nằm trong chương về Việt Nam thì market là Việt Nam.
7. period: kỳ đo viết dạng "2024", "Q1 2025", "H1 2026", "2025-03"; tăng trưởng so sánh thì ghi cả hai kỳ,
   ví dụ "Q1 2025 vs Q4 2024". Số dự báo ghi năm dự báo, ví dụ "2029".
8. section_title: tên chương hoặc tiêu đề bảng chứa câu trích, chép nguyên văn từ tài liệu; để trống nếu không có.
9. attributed_to: nếu tài liệu ghi số liệu là của một hãng khác (ví dụ "according to Sensor Tower"), ghi tên hãng đó.
10. criterion: số thứ tự tiêu chí mà nhận định phục vụ, -1 nếu không thuộc tiêu chí nào.
11. genre và genre_level: thể loại nếu số liệu là của một thể loại (genre) hoặc phân nhánh nhỏ (subgenre), còn không
    thì để trống và ghi "all"."""


FOLLOWUP_SCHEMA = {**PLAN_SCHEMA, "properties": {**PLAN_SCHEMA["properties"], "standalone_question": {"type": "string"}},
                   "required": PLAN_SCHEMA["required"] + ["standalone_question"]}

FOLLOWUP_PROMPT = """Bạn hỗ trợ chuyên viên phát triển kinh doanh của một nhà phát hành game ở Việt Nam nghiên cứu thị trường.
Hôm nay là {today}. Người dùng đang nghiên cứu tiếp từ một câu hỏi trước.

Câu hỏi trước: "{prev_question}"
Tiêu chí trước: {prev_criteria}
Thị trường trước: {prev_market}. Thể loại trước: {prev_genre}.
Những gì đã có số liệu kiểm chứng: {known}

Câu hỏi tiếp theo của người dùng: "{follow}"

Hãy:
- standalone_question: viết lại câu hỏi tiếp theo thành một câu hỏi tiếng Việt đầy đủ, tự hiểu được mà không cần
  câu hỏi trước. Giữ nguyên những gì câu hỏi tiếp theo không đổi (chỉ số, kỳ đo, thị trường, thể loại); chỉ đổi
  phần người dùng muốn đổi. Không trả lời câu hỏi.
- criteria: 2 đến 4 tiêu chí đo được cho câu hỏi đầy đủ đó, viết tiếng Việt, ngắn gọn.
- queries: 3 truy vấn tìm kiếm web tiếng Anh để tìm số liệu CÒN THIẾU (không tìm lại những gì đã có), ưu tiên
  báo cáo của hãng dữ liệu (Sensor Tower, Newzoo, Niko Partners, data.ai, AppMagic).
- market, genre: của câu hỏi đầy đủ; để trống nếu không rõ."""


def plan_followup(llm: LLM, prev: dict, follow: str, today: date | None = None) -> dict:
    """Plan a follow-up question in the context of the previous run."""
    today = today or date.today()
    known = sorted({f["label"] for f in prev.get("findings", [])})[:15]
    p = prev["plan"]
    out = llm.json(FOLLOWUP_PROMPT.format(
        today=today.isoformat(), prev_question=prev["question"], prev_criteria="; ".join(p.get("criteria", [])),
        prev_market=p.get("market") or "chưa rõ", prev_genre=p.get("genre") or "không giới hạn",
        known="; ".join(known) or "(chưa có)", follow=follow), FOLLOWUP_SCHEMA)
    out["criteria"] = [c for c in out.get("criteria", []) if c.strip()][:5] or list(p.get("criteria", []))
    out["queries"] = [q for q in out.get("queries", []) if q.strip()][:5]
    out["standalone_question"] = (out.get("standalone_question") or "").strip() or follow
    return out


def _int(x) -> int:
    try:
        return int(x)
    except (TypeError, ValueError):
        return -1


def plan(llm: LLM, question: str, today: date | None = None) -> dict:
    today = today or date.today()
    out = llm.json(PLAN_PROMPT.format(question=question, today=today.isoformat()), PLAN_SCHEMA)
    out["criteria"] = [c for c in out.get("criteria", []) if c.strip()][:5]
    out["queries"] = [q for q in out.get("queries", []) if q.strip()][:5]
    return out


def _keywords(question: str, criteria: list[str]) -> list[str]:
    words = re.findall(r"[a-zA-ZÀ-ỹ]{4,}", (question + " " + " ".join(criteria)).lower())
    base = ["revenue", "growth", "market", "mobile", "billion", "million", "genre", "downloads",
            "doanh thu", "tăng trưởng", "thị trường", "southeast asia", "vietnam"]
    return list(dict.fromkeys(words + base))


def select_chunks(text: str, keywords: list[str], k: int = MAX_CHUNKS_PER_SOURCE) -> list[str]:
    if len(text) <= CHUNK_CHARS:
        return [text]
    chunks = []
    pos = 0
    while pos < len(text):
        end = min(len(text), pos + CHUNK_CHARS)
        if end < len(text):
            cut = text.rfind("\n", pos + CHUNK_CHARS // 2, end)
            end = cut if cut > 0 else end
        chunks.append(text[pos:end])
        pos = end
    low = [c.lower() for c in chunks]
    scores = [sum(c.count(w) for w in keywords) + len(re.findall(r"\d+(?:[.,]\d+)?\s*(?:%|billion|million|tỷ|triệu)", c))
              for c in low]
    best = sorted(range(len(chunks)), key=lambda i: -scores[i])[:k]
    return [chunks[i] for i in sorted(best)]


def extract_claims(llm: LLM, question: str, criteria: list[str], source: Source, start_index: int = 1) -> list[Claim]:
    claims: list[Claim] = []
    crit = "; ".join(f"{i}. {c}" for i, c in enumerate(criteria))
    for chunk in select_chunks(source.text, _keywords(question, criteria)):
        out = llm.json(EXTRACT_PROMPT.format(
            question=question, criteria=crit, title=source.title or source.domain, url=source.url,
            published=source.published or "không rõ", text=chunk), CLAIM_SCHEMA)
        for c in out.get("claims", []):
            claims.append(Claim(
                id=f"C{start_index + len(claims)}", source_id=source.id,
                claim_text=c.get("claim_text", ""), metric=c.get("metric", "other"),
                value_text=c.get("value_text", ""), market=c.get("market", ""), period=c.get("period", ""),
                scope=c.get("scope", "unknown"), genre=c.get("genre", ""), genre_level=c.get("genre_level", "all"),
                quote=c.get("quote", ""), section_title=c.get("section_title", ""),
                attributed_to=c.get("attributed_to", ""), criterion=_int(c.get("criterion")),
            ))
    return claims
