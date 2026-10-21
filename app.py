"""Streamlit UI: question -> plan (user reviews) -> run -> brief with checkable claims."""
from __future__ import annotations

import json
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
try:  # Streamlit Community Cloud keeps keys in st.secrets
    for k, v in st.secrets.items():
        if isinstance(v, str):
            os.environ.setdefault(k, v)
except Exception:
    pass

from core import extract, pipeline, store  # noqa: E402
from core.evidence import evidence_url  # noqa: E402
from core.fetch import from_upload  # noqa: E402
from core.llm import LLM, LLMError  # noqa: E402
from core.report import brief_markdown  # noqa: E402
from core.search import search_engine_name  # noqa: E402
from core.textnorm import fmt_value  # noqa: E402

SAMPLES = [
    "Thể loại game mobile nào có tiềm năng tại Đông Nam Á trong 12 tháng tới?",
    "Quy mô thị trường game Đông Nam Á năm 2024 là bao nhiêu và các nguồn có khớp nhau không?",
    "Thể loại game mobile nào tăng trưởng doanh thu nhanh nhất ở Đông Nam Á trong 12 tháng qua?",
    "Có nên phát hành game MOBA trên mobile tại Việt Nam trong 12 tháng tới không?",
    "Doanh thu tháng 9/2026 của tựa game Tiếu Ngạo tại Việt Nam là bao nhiêu?",
]
TIER_HELP = "A: dữ liệu gốc. B: thứ cấp uy tín. C: blog, ý kiến. D: không dùng làm bằng chứng."

st.set_page_config(page_title="Nghiên cứu thị trường game", layout="wide")
ss = st.session_state
ss.setdefault("plan", None)
ss.setdefault("result", None)


@st.cache_resource
def get_llm():
    return LLM()


def research_further(prev: dict, follow_question: str = "", queries: list[str] | None = None) -> None:
    with st.status("Đang nghiên cứu tiếp, giữ bối cảnh lần trước", expanded=True) as status:
        res = pipeline.follow_up(prev, follow_question, queries, use_search=use_search, max_sources=max_sources,
                                 llm=llm, progress=st.write)
        status.update(label="Xong", state="complete", expanded=False)
    store.save(res)
    ss.result = res
    ss.plan = res["plan"]
    st.rerun()


# ---------- sidebar ----------
with st.sidebar:
    st.header("Cài đặt")
    try:
        llm = get_llm()
        st.caption(f"Mô hình: {llm.provider}/{llm.model}")
    except LLMError as e:
        llm = None
        st.error(str(e))
    use_search = st.checkbox("Tìm nguồn trên web", value=True, help=f"Đang dùng {search_engine_name()}")
    max_sources = st.slider("Số nguồn tối đa mỗi lần chạy", 3, 12, 6)
    st.caption(TIER_HELP)
    st.divider()
    st.subheader("Lần chạy trước")
    for rid, created, q in store.recent(10):
        if st.button(f"{created[5:16]}  {q[:40]}", key=f"h{rid}"):
            ss.result = store.load(rid)
            ss.plan = ss.result["plan"]

# ---------- input ----------
st.title("Trợ lý nghiên cứu thị trường game")
st.caption("Mỗi nhận định phải có câu trích nguyên văn được code tìm thấy trong nguồn; "
           "hạng nguồn và mức tin cậy tính bằng quy tắc, không do AI tự chấm.")

sample = st.selectbox("Câu hỏi mẫu", ["(tự nhập)"] + SAMPLES)
question = st.text_area("Câu hỏi nghiên cứu", value="" if sample == "(tự nhập)" else sample, height=70)
with st.expander("Thêm nguồn của bạn (link hoặc file báo cáo)"):
    urls_text = st.text_area("Link, mỗi dòng một link", height=80)
    files = st.file_uploader("Tải lên PDF hoặc TXT", type=["pdf", "txt", "md"], accept_multiple_files=True)
    upload_tier = st.selectbox("Hạng cho file tải lên", ["A", "B", "C"], index=1, help=TIER_HELP)

col1, col2 = st.columns(2)
if col1.button("1. Lập kế hoạch", disabled=not (question.strip() and llm)):
    with st.spinner("Đang tách tiêu chí và viết truy vấn"):
        ss.plan = extract.plan(llm, question)
        ss.plan_question = question
        ss.result = None

if ss.plan:
    st.subheader("Kế hoạch (bạn có thể sửa trước khi chạy)")
    c1, c2 = st.columns(2)
    crit = c1.text_area("Tiêu chí ra quyết định, mỗi dòng một tiêu chí", "\n".join(ss.plan["criteria"]), height=130)
    qs = c2.text_area("Truy vấn tìm kiếm, mỗi dòng một truy vấn", "\n".join(ss.plan["queries"]), height=130)
    ss.plan["criteria"] = [x.strip() for x in crit.splitlines() if x.strip()]
    ss.plan["queries"] = [x.strip() for x in qs.splitlines() if x.strip()]
    st.caption(f"Thị trường: {ss.plan.get('market') or 'chưa rõ'}. Thể loại: {ss.plan.get('genre') or 'không giới hạn'}.")

    if col2.button("2. Chạy nghiên cứu", type="primary", disabled=llm is None):
        uploads = []
        for f in files or []:
            s = from_upload(f.name, f.getvalue())
            if s.error:
                st.warning(f"{f.name}: {s.error}")
            uploads.append(s)
        with st.status("Đang chạy", expanded=True) as status:
            res = pipeline.run(question, plan=ss.plan, extra_urls=urls_text.splitlines(), uploads=uploads,
                               use_search=use_search, max_sources=max_sources, llm=llm,
                               upload_tier=upload_tier, progress=st.write)
            status.update(label="Xong", state="complete", expanded=False)
        store.save(res)
        ss.result = res

# ---------- result ----------
r = ss.result
if r:
    b = r["brief"]
    claims = {c["id"]: c for c in r["claims"]}
    sources = {s["id"]: s for s in r["sources"]}
    trusted, uncertain, steps = b.get("trusted", []), b.get("uncertain", []), b.get("next_steps", [])
    st.divider()
    if len(r.get("thread") or []) > 1:
        st.caption("Chuỗi nghiên cứu: " + "  →  ".join(t["question"] for t in r["thread"]))
    st.subheader("Bản tóm tắt quyết định")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Kết luận", b["decision"])
    m2.metric("Mức tin cậy", b["confidence"])
    m3.metric("Có thể tin / Chưa chắc chắn", f"{len(trusted)} / {len(uncertain)}")
    m4.metric("Nhận định giữ / loại", f"{r['stats']['verified']} / {r['stats']['rejected']}")
    if r["stats"]["sources_failed"]:
        st.warning(f"{r['stats']['sources_failed']} nguồn bị lỗi khi đọc hoặc khi trích nhận định. "
                   "Xem lý do ở tab Nguồn.")
    st.write(b["summary"])
    st.caption(f"Khung thời gian dữ liệu: {r['window']['label']}"
               + (f". Giữ lại {r['stats']['carried']} nhận định đã kiểm từ lần trước." if r["stats"].get("carried") else ""))
    if b["reasons"]:
        st.markdown("**Lý do chính** (✅ dựa trên nhận định có thể tin, ⚠️ có nhận định chưa chắc chắn)")
        for i, x in enumerate(b["reasons"], 1):
            mark = {"trusted": "✅ ", "uncertain": "⚠️ "}.get(x.get("status"), "")
            st.markdown(f"{i}. {mark}{x['text']} `{', '.join(x['claim_ids'])}`")

    col_t, col_u = st.columns(2)
    with col_t:
        st.markdown("#### ✅ Có thể tin")
        st.caption("Ít nhất một nguồn gốc hạng A/B, không mâu thuẫn, không lệch kỳ đo hay thị trường, "
                   "không phải số dẫn lại chưa đối chiếu. Do code xếp, không phải AI.")
        for x in trusted:
            st.markdown(f"**{x['finding']}. {x['label']}**: {x['values']} ({', '.join(x['origins'])}). "
                        f"Tin cậy {x['confidence']}. `{', '.join(x['claim_ids'])}`")
            for n in x.get("notes", []):
                st.caption(f"Lưu ý: {n}")
        if not trusted:
            st.write("Chưa có số liệu nào đủ điều kiện.")
    with col_u:
        st.markdown("#### ⚠️ Chưa chắc chắn")
        st.caption("Có số liệu đã kiểm câu trích nhưng còn lý do để chưa tin hẳn.")
        for x in uncertain:
            st.markdown(f"**{x['finding']}. {x['label']}**: {x['values']} ({', '.join(x['origins'])}). "
                        f"`{', '.join(x['claim_ids'])}`")
            for w in x["why"]:
                st.markdown(f"  - {w}")
        if not uncertain:
            st.write("Không có.")
    other = b.get("other", [])
    if other:
        with st.expander(f"Số liệu khác đã kiểm nhưng ngoài phạm vi câu hỏi ({len(other)})"):
            for x in other:
                st.markdown(f"- **{x['finding']}. {x['label']}**: {x['values']} ({', '.join(x['origins'])}). {x['why'][0]}.")

    st.markdown("#### 🔎 Nên tìm hiểu tiếp ở đâu")
    st.caption("Bấm để nghiên cứu tiếp: hệ thống giữ câu hỏi, các nhận định đã kiểm và các nhận định bạn đã loại, "
               "chỉ tìm thêm phần còn thiếu.")

    def show_step(i: int, s: dict) -> None:
        c_text, c_btn = st.columns([5, 1])
        about = f" ({', '.join(s['findings'])})" if s.get("findings") else ""
        c_text.markdown(f"- {s['text']}{about}" + (f"  \n  Truy vấn: `{s['query']}`" if s["query"] else ""))
        if s["url"]:
            c_btn.link_button("Mở nguồn", s["url"])
        elif s["query"] and c_btn.button("Tìm thêm", key=f"q{r['id']}{i}", disabled=llm is None or not use_search):
            research_further(r, queries=[s["query"]])
        elif s["ask"] and c_btn.button("Tìm thêm", key=f"a{r['id']}{i}", disabled=llm is None):
            research_further(r, follow_question=s["ask"])

    for i, s in enumerate(steps[:5]):
        show_step(i, s)
    if len(steps) > 5:
        with st.expander(f"Các bước khác ({len(steps) - 5})"):
            for i, s in enumerate(steps[5:], 5):
                show_step(i, s)
    if not steps:
        st.write("Không có bước nào cần thêm.")
    with st.form(f"follow{r['id']}", clear_on_submit=True):
        fq = st.text_input("Hỏi tiếp, giữ bối cảnh câu hỏi này",
                           placeholder="Ví dụ: Còn riêng Việt Nam thì sao? Hoặc: Số năm 2025 có chưa?")
        asked = st.form_submit_button("Hỏi tiếp", disabled=llm is None)
    if asked and fq.strip():
        research_further(r, follow_question=fq)
    if b["conflicts"]:
        st.markdown("**Mâu thuẫn giữa các nguồn**")
        for x in b["conflicts"]:
            st.markdown(f"- {x}")
    if b["definition_notes"]:
        st.markdown("**Số liệu khác định nghĩa, không so trực tiếp**")
        for x in b["definition_notes"]:
            st.markdown(f"- {x}")
    if b["gaps"]:
        st.markdown("**Tiêu chí chưa có dữ liệu đã kiểm**")
        for x in b["gaps"]:
            st.markdown(f"- {x}")
    if b["what_would_change"]:
        st.markdown("**Điều gì sẽ làm thay đổi khuyến nghị**")
        for x in b["what_would_change"]:
            st.markdown(f"- {x}")
    if b["guard_log"]:
        with st.expander(f"Câu bị bộ kiểm loại khỏi bản tóm tắt ({len(b['guard_log'])})"):
            for x in b["guard_log"]:
                st.markdown(f"- {x}")

    t1, t2, t3, t4 = st.tabs(["Nhận định đã kiểm", "Nhận định bị loại", "Nguồn", "Nhật ký chạy"])
    with t1:
        st.caption("Mở từng nhận định để xem câu trích và link nguồn. Đánh dấu nhận định sai rồi viết lại bản tóm tắt.")
        excluded = set()
        for f in r["findings"]:
            st.markdown(f"**{f['key']}. {f['label']}**: tin cậy {f['confidence']}, "
                        f"{'mâu thuẫn' if f['status'] == 'conflict' else 'khớp' if f['status'] == 'agree' else 'một nguồn gốc'}. "
                        f"{'; '.join(f['reasons'])}")
            for cid in f["claim_ids"]:
                c = claims[cid]
                s = sources[c["source_id"]]
                head = f"{cid}  {c['value_text']}  ({c['origin']}, hạng {c['tier']})" + ("  có cảnh báo" if c["flags"] else "")
                with st.expander(head):
                    st.write(c["claim_text"])
                    st.markdown(f"> {c['quote']}")
                    page = f", trang {c['page']}" if c.get("page") else ""
                    st.markdown(f"Nguồn: [{s['title'] or s['domain']}]({s['url']}){page}, đăng {s['published'] or 'không rõ'}. "
                                f"Giá trị chuẩn hóa: {fmt_value(c['value'], c['unit'])}. Kỳ: {c['period']}. "
                                f"Thị trường: {c['market']}. Phạm vi: {c['scope']}.")
                    link = evidence_url(s["url"], s["kind"], c["quote"], c.get("page"))
                    if link:
                        st.link_button("Mở nguồn tại câu trích" if s["kind"] != "pdf" else f"Mở PDF ở trang {c['page']}",
                                       link)
                    if c.get("context"):
                        st.caption("Đoạn văn quanh câu trích, lấy nguyên từ nguồn (câu trích nằm trong 【 】):")
                        st.text(c["context"].replace(c["quote"], f"【{c['quote']}】", 1))
                    if c.get("section_title"):
                        st.caption(f"Chương/bảng: {c['section_title']}")
                    for fl in c["flags"]:
                        st.warning(fl)
                    if st.checkbox("Loại nhận định này", key=f"x{r['id']}{cid}", value=c.get("excluded_by_user", False)):
                        excluded.add(cid)
        if r["findings"] and st.button("Viết lại bản tóm tắt sau khi loại", disabled=llm is None):
            ss.result = pipeline.rebrief(r, excluded, llm)
            store.save(ss.result)
            st.rerun()
        if not r["findings"]:
            st.info("Không có nhận định nào qua được bước kiểm câu trích.")
    with t2:
        rej = [c for c in r["claims"] if not c["verified"]]
        if rej:
            st.dataframe(pd.DataFrame([{
                "Mã": c["id"], "Nhận định": c["claim_text"], "Giá trị": c["value_text"],
                "Lý do loại": c["verify_note"], "Câu trích AI đưa ra": c["quote"],
                "Nguồn": sources[c["source_id"]]["domain"]} for c in rej]), hide_index=True, width="stretch")
        else:
            st.write("Không có nhận định nào bị loại.")
    with t3:
        st.dataframe(pd.DataFrame([{
            "Nguồn": s["title"] or s["url"], "Tên miền": s["domain"], "Hạng": s["tier"],
            "Vì sao": "; ".join(s["tier_notes"]), "Ngày đăng": s["published"], "Lỗi": s["error"] or "",
            "Link": s["url"]} for s in r["sources"]]), hide_index=True, width="stretch")
        if r["skipped"]:
            st.markdown("**Không đọc**")
            for x in r["skipped"]:
                st.markdown(f"- {x['url']}: {x['reason']}")
    with t4:
        st.json(r["stats"])
        st.json({"plan": r["plan"], "search": r["search_log"]})

    d1, d2 = st.columns(2)
    d1.download_button("Tải bản tóm tắt (Markdown)", brief_markdown(r), file_name=f"tom-tat-{r['id']}.md")
    d2.download_button("Tải toàn bộ kết quả (JSON)", json.dumps(r, ensure_ascii=False, indent=1),
                       file_name=f"ket-qua-{r['id']}.json")
