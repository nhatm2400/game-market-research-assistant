"""Render a run as a Markdown brief that can be downloaded or pasted into a report."""
from __future__ import annotations

from .textnorm import fmt_value


def brief_markdown(r: dict) -> str:
    b = r["brief"]
    claims = {c["id"]: c for c in r["claims"]}
    sources = {s["id"]: s for s in r["sources"]}
    out = [f"# Bản tóm tắt quyết định", "",
           f"**Câu hỏi:** {r['question']}", "",
           f"**Khuyến nghị:** {b['decision']}. **Mức tin cậy:** {b['confidence']}.", "",
           b["summary"] or "", "",
           f"Khung thời gian dữ liệu: {r['window']['label']}. Ngày chạy: {r['today']}.", ""]
    if b["reasons"]:
        out += ["## Lý do chính", ""]
        for i, x in enumerate(b["reasons"], 1):
            out.append(f"{i}. {x['text']} [{', '.join(x['claim_ids'])}]")
        out.append("")
    if b["conflicts"]:
        out += ["## Mâu thuẫn giữa các nguồn", ""] + [f"- {x}" for x in b["conflicts"]] + [""]
    if b["definition_notes"]:
        out += ["## Số liệu khác định nghĩa (không so trực tiếp)", ""] + [f"- {x}" for x in b["definition_notes"]] + [""]
    if b["gaps"]:
        out += ["## Tiêu chí chưa có dữ liệu đã kiểm", ""] + [f"- {x}" for x in b["gaps"]] + [""]
    if b["what_would_change"]:
        out += ["## Điều gì sẽ làm thay đổi khuyến nghị", ""] + [f"- {x}" for x in b["what_would_change"]] + [""]
    cited = [cid for x in b["reasons"] for cid in x["claim_ids"]]
    if cited:
        out += ["## Nhận định được trích dẫn", ""]
        for cid in dict.fromkeys(cited):
            c = claims[cid]
            s = sources.get(c["source_id"], {})
            page = f", trang {c['page']}" if c.get("page") else ""
            out.append(f"- **{cid}** {c['claim_text']} Giá trị: {c['value_text']} ({fmt_value(c['value'], c['unit'])}). "
                       f"Nguồn gốc: {c['origin']}, hạng {c['tier']}. Nguồn: {s.get('url', '')}{page}, "
                       f"đăng {s.get('published') or 'không rõ'}.")
            out.append(f"  > {c['quote']}")
            for f in c.get("flags", []):
                out.append(f"  - Cảnh báo: {f}")
        out.append("")
    if b["guard_log"]:
        out += ["## Câu bị bộ kiểm loại khỏi bản tóm tắt", ""] + [f"- {x}" for x in b["guard_log"]] + [""]
    st = r["stats"]
    out.append(f"_Đọc {st['sources_read']} nguồn, trích {st['claims']} nhận định, giữ {st['verified']}, "
               f"loại {st['rejected']}. {st['llm_calls']} lượt gọi {st['model']}, {st['seconds']} giây._")
    return "\n".join(out)
