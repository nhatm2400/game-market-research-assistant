"""Render a run as a Markdown brief that can be downloaded or pasted into a report."""
from __future__ import annotations

from .evidence import evidence_url
from .textnorm import fmt_value


def brief_markdown(r: dict) -> str:
    b = r["brief"]
    claims = {c["id"]: c for c in r["claims"]}
    sources = {s["id"]: s for s in r["sources"]}
    out = [f"# Bản tóm tắt quyết định", "",
           f"**Câu hỏi:** {r['question']}", ""]
    if len(r.get("thread") or []) > 1:
        out += ["**Chuỗi nghiên cứu:** " + " → ".join(t["question"] for t in r["thread"]), ""]
    out += [f"**Kết luận:** {b['decision']}. **Mức tin cậy:** {b['confidence']}.", "",
            b["summary"] or "", ""]
    card = b.get("card")
    if card:
        out += ["## Quyết định nhanh", "", f"**Nên làm gì tiếp:** {card['action']}"]
        if card["next_step"]:
            s = card["next_step"]
            out.append(f"Bước tiếp theo: {s['text']}." + (f" Truy vấn gợi ý: `{s['query']}`." if s["query"] else "")
                       + (f" {s['url']}" if s["url"] else ""))
        out += ["", "**Dựa trên bằng chứng nào:**", ""]
        label = {"trusted": "có thể tin", "uncertain": "chưa chắc chắn"}
        for e in card["evidence"]:
            why_txt = f", vì: {e['why']}" if e.get("why") and e["status"] == "uncertain" else ""
            out.append(f"- {e['values']}: {e['label']} (hạng {e['tier']}, {label[e['status']]}{why_txt}).")
            out += [f"  - {x['origin']}: {x['value']} [{x['claim_id']}] {x['url']}".rstrip() for x in e.get("links", [])]
        if not card["evidence"]:
            out.append("- Chưa có nhận định nào đã kiểm.")
        out.append("")
    out += [f"Khung thời gian dữ liệu: {r['window']['label']}. Ngày chạy: {r['today']}.", ""]
    if b["reasons"]:
        out += ["## Lý do chính", ""]
        for i, x in enumerate(b["reasons"], 1):
            mark = {"trusted": " (có thể tin)", "uncertain": " (chưa chắc chắn)"}.get(x.get("status"), "")
            out.append(f"{i}. {x['text']} [{', '.join(x['claim_ids'])}]{mark}")
        out.append("")
    if "trusted" in b:
        out += ["## Có thể tin", ""]
        for x in b["trusted"]:
            out.append(f"- **{x['finding']}** {x['label']}: {x['values']} ({', '.join(x['origins'])}), "
                       f"tin cậy {x['confidence']}. [{', '.join(x['claim_ids'])}]")
            out += [f"  - Lưu ý: {n}" for n in x.get("notes", [])]
        out += (["- Chưa có"] if not b["trusted"] else []) + [""]
        out += ["## Chưa chắc chắn", ""]
        for x in b["uncertain"]:
            out.append(f"- **{x['finding']}** {x['label']}: {x['values']} ({', '.join(x['origins'])}). "
                       f"[{', '.join(x['claim_ids'])}]")
            out += [f"  - {w}" for w in x["why"]]
        out += (["- Không có"] if not b["uncertain"] else []) + [""]
        if b.get("other"):
            out += ["## Số liệu khác, ngoài phạm vi câu hỏi", ""]
            out += [f"- **{x['finding']}** {x['label']}: {x['values']} ({', '.join(x['origins'])}). {x['why'][0]}."
                    for x in b["other"]] + [""]
        out += ["## Nên tìm hiểu tiếp ở đâu", ""]
        for s in b["next_steps"]:
            about = f" ({', '.join(s['findings'])})" if s.get("findings") else ""
            extra = f" Truy vấn gợi ý: `{s['query']}`." if s["query"] else (f" {s['url']}" if s["url"] else "")
            out.append(f"- {s['text']}{about}.{extra}")
        out += (["- Không có"] if not b["next_steps"] else []) + [""]
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
            link = evidence_url(s.get("url", ""), s.get("kind", ""), c["quote"], c.get("page")) or s.get("url", "")
            out.append(f"- **{cid}** {c['claim_text']} Giá trị: {c['value_text']} ({fmt_value(c['value'], c['unit'])}). "
                       f"Nguồn gốc: {c['origin']}, hạng {c['tier']}. Nguồn: {link}{page}, "
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
