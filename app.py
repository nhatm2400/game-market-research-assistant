"""Streamlit UI: question -> plan (user reviews) -> run -> brief with checkable claims."""
from __future__ import annotations

import json
import os
from pathlib import Path
from html import escape as h

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
from core.brief import UNSURE  # noqa: E402
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
CONF_LEVEL = {"Thấp": 1, "Trung bình": 2, "Cao": 3}

# Colour carries meaning only: jade = can be trusted, ochre = not settled, slate = outside the question or
# missing, indigo = something to do. The serif face is kept for words quoted from a source.
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,400;7..72,500&display=swap');
:root { --ink:#1A2433; --muted:#5B6675; --line:#D5DDE3; --jade:#17785B; --ochre:#95600F;
        --slate:#66717E; --indigo:#3346A8; }
.lead { font-size:1.05rem; color:var(--muted); max-width:68ch; margin:-.4rem 0 1.2rem; line-height:1.55; }
.thread { color:var(--muted); font-size:.9rem; margin:.2rem 0 .8rem; }
.thread b { color:var(--ink); font-weight:600; }
.verdict { border-top:3px solid var(--ink); padding:1rem 0 .2rem; margin:.4rem 0 1rem; }
.v-label { color:var(--muted); font-size:.9rem; }
.v-answer { font-size:2.1rem; font-weight:700; line-height:1.15; letter-spacing:-.015em; margin:.15rem 0 .5rem; }
.v-answer.firm { color:var(--ink); } .v-answer.unsure { color:var(--ochre); } .v-answer.missing { color:var(--slate); }
.v-conf { display:flex; align-items:center; gap:.6rem; font-weight:500; margin-bottom:.8rem; }
.meter { display:inline-flex; gap:3px; }
.meter i { width:26px; height:8px; border-radius:2px; background:var(--line); }
.meter.l1 i:nth-child(-n+1), .meter.l2 i:nth-child(-n+2), .meter.l3 i:nth-child(-n+3) { background:var(--indigo); }
.v-summary { font-size:1.08rem; line-height:1.6; max-width:72ch; margin:0 0 .6rem; }
.v-meta { color:var(--muted); font-size:.9rem; max-width:80ch; margin:0; }
.reason { display:flex; gap:.65rem; margin:.45rem 0; max-width:80ch; line-height:1.5; }
.dot { flex:none; width:.6rem; height:.6rem; border-radius:50%; margin-top:.45rem; }
.dot.trusted { background:var(--jade); } .dot.uncertain { background:var(--ochre); }
.chip { display:inline-block; font-size:.75rem; line-height:1.35; padding:0 .35rem; margin-left:.25rem;
        border:1px solid var(--line); border-radius:3px; color:var(--muted); white-space:nowrap; }
.col-head { font-size:1.15rem; font-weight:700; padding-bottom:.35rem; border-bottom:2px solid; margin:.6rem 0 .3rem; }
.col-head.trusted { color:var(--jade); } .col-head.uncertain { color:var(--ochre); } .col-head.next { color:var(--indigo); }
.col-head span { font-weight:500; color:var(--muted); font-size:.95rem; margin-left:.35rem; }
.col-note { color:var(--muted); font-size:.85rem; margin:0 0 .9rem; line-height:1.45; }
.ev { border-left:3px solid var(--line); padding:.15rem 0 .2rem .85rem; margin:0 0 1.05rem; }
.ev.trusted { border-color:var(--jade); } .ev.uncertain { border-color:var(--ochre); }
.ev-what { color:var(--muted); font-size:.9rem; line-height:1.4; }
.ev-val { font-size:1.4rem; font-weight:600; font-variant-numeric:tabular-nums; line-height:1.3; margin:.1rem 0; }
.ev-src { font-size:.9rem; display:flex; align-items:center; flex-wrap:wrap; gap:.15rem; }
.ev ul { margin:.35rem 0 0; padding-left:1.1rem; color:var(--muted); font-size:.88rem; line-height:1.45; }
.ev ul li { margin:.1rem 0; }
.seal { display:inline-flex; align-items:center; justify-content:center; width:1.3rem; height:1.3rem;
        border-radius:50%; border:1.5px solid currentColor; font-size:.7rem; font-weight:700; margin-right:.3rem; }
.seal.A { color:var(--jade); } .seal.B { color:var(--indigo); } .seal.C { color:var(--ochre); } .seal.D { color:#9AA3AD; }
.step { line-height:1.5; max-width:80ch; padding:.15rem 0; }
.step small { display:block; color:var(--muted); }
.src-quote { font-family:'Literata', Georgia, serif; font-size:1.04rem; line-height:1.7; border-left:2px solid var(--ink);
             padding:.1rem 0 .1rem .9rem; margin:.4rem 0 .8rem; max-width:75ch; }
.src-context { font-family:'Literata', Georgia, serif; font-size:.92rem; line-height:1.7; color:var(--muted);
               max-width:75ch; white-space:pre-wrap; max-height:14rem; overflow:auto; }
.src-context mark { background:#E7F3EE; color:var(--ink); padding:0 .1rem; }
@media (prefers-reduced-motion: reduce) { * { transition:none !important; animation:none !important; } }
</style>
"""

st.set_page_config(page_title="Nghiên cứu thị trường game", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
ss = st.session_state
ss.setdefault("plan", None)
ss.setdefault("result", None)


@st.cache_resource
def get_llm():
    return LLM()


@st.cache_data
def examples() -> dict[str, dict]:
    """Live runs of the test cases stored in the repo, so the demo shows results without spending LLM quota."""
    files = sorted(Path(__file__).parent.glob("eval/results/TC*.json"), key=lambda p: int(p.stem[2:]))
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in files}


def research_further(prev: dict, follow_question: str = "", queries: list[str] | None = None) -> None:
    with st.status("Đang nghiên cứu tiếp, giữ bối cảnh lần trước", expanded=True) as status:
        try:
            res = pipeline.follow_up(prev, follow_question, queries, use_search=use_search, max_sources=max_sources,
                                     llm=llm, progress=st.write)
        except LLMError as e:
            status.update(label="Chưa nghiên cứu tiếp được", state="error")
            st.error(str(e))
            return
        status.update(label="Xong", state="complete", expanded=False)
    store.save(res)
    ss.result = res
    ss.plan = res["plan"]
    st.rerun()


def chips(ids) -> str:
    return "".join(f'<span class="chip">{h(i)}</span>' for i in ids)


def evidence_row(x: dict, kind: str, claims: dict, notes: list[str]) -> str:
    """One finding: what it measures, its value, the best source tier, its origin and why it sits here."""
    tier = min(claims[c]["tier"] for c in x["claim_ids"])
    items = "".join(f"<li>{h(n)}</li>" for n in notes)
    return (f'<div class="ev {kind}"><div class="ev-what">{h(x["label"])}</div>'
            f'<div class="ev-val">{h(x["values"])}</div>'
            f'<div class="ev-src"><span class="seal {h(tier)}" title="Hạng nguồn {h(tier)}">{h(tier)}</span>'
            f'{h(", ".join(x["origins"]))}{chips([x["finding"]] + x["claim_ids"])}</div>'
            + (f"<ul>{items}</ul>" if items else "") + "</div>")


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
    runs = store.recent(10)
    if runs:
        st.subheader("Lần chạy trước")
    for rid, created, q in runs:
        if st.button(f"{created[5:16]}  {q[:40]}", key=f"h{rid}"):
            ss.result = store.load(rid)
            ss.plan = ss.result["plan"]
    st.subheader("Kết quả mẫu đã chạy thật")
    st.caption("Các tình huống kiểm thử trong repo, mở ngay, không tốn lượt gọi AI. Vẫn hỏi tiếp được từ đây.")
    for tc, ex in examples().items():
        if st.button(f"{tc}  {ex['question'][:45]}", key=f"e{tc}"):
            ss.result, ss.plan = ex, None   # no plan editor, so the result sits right under the question box

# ---------- input ----------
st.title("Trợ lý nghiên cứu thị trường game")
st.markdown('<p class="lead">Đặt một câu hỏi, hệ thống đọc nguồn rồi tách điều có thể tin khỏi điều còn chưa chắc '
            'chắn. Mỗi con số đi kèm câu trích nguyên văn mà code đã tìm thấy trong nguồn; hạng nguồn và mức tin cậy '
            'tính bằng quy tắc, không do AI tự chấm.</p>', unsafe_allow_html=True)
if not ss.plan and not ss.result:
    st.caption("Muốn xem ngay mà không chờ chạy: mở một kết quả mẫu đã chạy thật ở thanh bên trái.")

sample = st.selectbox("Câu hỏi mẫu", ["(tự nhập)"] + SAMPLES)
question = st.text_area("Câu hỏi nghiên cứu", value="" if sample == "(tự nhập)" else sample, height=70)
with st.expander("Thêm nguồn của bạn (link hoặc file báo cáo)"):
    urls_text = st.text_area("Link, mỗi dòng một link", height=80)
    files = st.file_uploader("Tải lên PDF hoặc TXT", type=["pdf", "txt", "md"], accept_multiple_files=True)
    upload_tier = st.selectbox("Hạng cho file tải lên", ["A", "B", "C"], index=1, help=TIER_HELP)

col1, col2 = st.columns(2)
if col1.button("1. Lập kế hoạch", disabled=not (question.strip() and llm)):
    with st.spinner("Đang tách tiêu chí và viết truy vấn"):
        try:
            ss.plan = extract.plan(llm, question)
            ss.plan_question = question
            ss.result = None
        except LLMError as e:
            st.error(f"{e} Trong lúc chờ, có thể mở một kết quả mẫu đã chạy thật ở thanh bên.")

if ss.plan:
    st.subheader("Kế hoạch, sửa được trước khi chạy")
    c1, c2 = st.columns(2)
    crit = c1.text_area("Tiêu chí, mỗi dòng một tiêu chí", "\n".join(ss.plan["criteria"]), height=130)
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

    if len(r.get("thread") or []) > 1:
        path = " → ".join(h(t["question"]) for t in r["thread"][:-1])
        st.markdown(f'<p class="thread">Nghiên cứu tiếp từ: {path} → <b>{h(r["thread"][-1]["question"])}</b></p>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<p class="thread">Câu hỏi: <b>{h(r["question"])}</b></p>', unsafe_allow_html=True)

    kind = ("unsure" if b["decision"] == UNSURE else "missing" if b["decision"] == "Cần thêm dữ liệu" else "firm")
    level = CONF_LEVEL.get(b["confidence"], 0)
    meta = (f"{len(trusted)} điều có thể tin, {len(uncertain)} điều chưa chắc chắn, {len(steps)} bước nên tìm tiếp. "
            f"Khung thời gian dữ liệu: {r['window']['label']}.")
    if r["stats"].get("carried"):
        meta += f" Giữ lại {r['stats']['carried']} nhận định đã kiểm từ lần trước."
    st.markdown(
        f'<section class="verdict"><div class="v-label">Kết luận</div>'
        f'<div class="v-answer {kind}">{h(b["decision"])}</div>'
        f'<div class="v-conf"><span class="meter l{level}" aria-hidden="true"><i></i><i></i><i></i></span>'
        f'Tin cậy {h(b["confidence"].lower() if level else b["confidence"])}</div>'
        + (f'<p class="v-summary">{h(b["summary"])}</p>' if b["summary"] else "")
        + f'<p class="v-meta">{h(meta)}</p></section>', unsafe_allow_html=True)
    if r["stats"]["sources_failed"]:
        st.warning(f"{r['stats']['sources_failed']} nguồn bị lỗi khi đọc hoặc khi trích nhận định. "
                   "Xem lý do ở tab Nguồn.")

    if b["reasons"]:
        rows = "".join(f'<div class="reason"><span class="dot {h(x.get("status", "uncertain"))}"></span>'
                       f'<div>{h(x["text"])}{chips(x["claim_ids"])}</div></div>' for x in b["reasons"])
        st.markdown(f'<div class="col-note">Lý do chính. Chấm xanh: dựa trên nhận định có thể tin. Chấm vàng: có '
                    f'nhận định chưa chắc chắn.</div>{rows}', unsafe_allow_html=True)

    col_t, col_u = st.columns(2, gap="large")
    with col_t:
        html = (f'<div class="col-head trusted">Có thể tin<span>{len(trusted)}</span></div>'
                '<p class="col-note">Nguồn gốc hạng A hoặc B, không mâu thuẫn, đúng kỳ và đúng thị trường câu hỏi.</p>')
        html += "".join(evidence_row(x, "trusted", claims, x.get("notes", [])) for x in trusted)
        st.markdown(html or "", unsafe_allow_html=True)
        if not trusted:
            st.caption("Chưa có số liệu nào đủ điều kiện. Xem cột bên cạnh và các bước nên tìm tiếp.")
    with col_u:
        html = (f'<div class="col-head uncertain">Chưa chắc chắn<span>{len(uncertain)}</span></div>'
                '<p class="col-note">Câu trích đã kiểm, nhưng còn lý do cụ thể để chưa tin hẳn.</p>')
        html += "".join(evidence_row(x, "uncertain", claims, x["why"]) for x in uncertain)
        st.markdown(html, unsafe_allow_html=True)
        if not uncertain:
            st.caption("Không có.")
    other = b.get("other", [])
    if other:
        with st.expander(f"Số liệu đã kiểm nhưng ngoài phạm vi câu hỏi ({len(other)})"):
            st.markdown("".join(evidence_row(x, "other", claims, x["why"]) for x in other), unsafe_allow_html=True)

    st.markdown(f'<div class="col-head next">Nên tìm hiểu tiếp ở đâu<span>{len(steps)}</span></div>'
                '<p class="col-note">Bấm để nghiên cứu tiếp. Hệ thống giữ câu hỏi, các nhận định đã kiểm và các nhận '
                'định bạn đã loại, chỉ tìm thêm phần còn thiếu.</p>', unsafe_allow_html=True)

    def show_step(i: int, s: dict) -> None:
        c_text, c_btn = st.columns([5, 1], vertical_alignment="center")
        extra = f"<small>Truy vấn: {h(s['query'])}</small>" if s["query"] else ""
        c_text.markdown(f'<div class="step">{h(s["text"])}{chips(s.get("findings", []))}{extra}</div>',
                        unsafe_allow_html=True)
        if s["url"]:
            c_btn.link_button("Mở nguồn", s["url"], width="stretch")
        elif s["query"] and c_btn.button("Tìm thêm", key=f"q{r['id']}{i}", disabled=llm is None or not use_search,
                                         width="stretch"):
            research_further(r, queries=[s["query"]])
        elif s["ask"] and c_btn.button("Tìm thêm", key=f"a{r['id']}{i}", disabled=llm is None, width="stretch"):
            research_further(r, follow_question=s["ask"])

    for i, s in enumerate(steps[:5]):
        show_step(i, s)
    if len(steps) > 5:
        with st.expander(f"Các bước khác ({len(steps) - 5})"):
            for i, s in enumerate(steps[5:], 5):
                show_step(i, s)
    if not steps:
        st.caption("Không còn bước nào cần làm thêm.")
    with st.form(f"follow{r['id']}", clear_on_submit=True, border=False):
        fq = st.text_input("Hỏi tiếp, giữ bối cảnh câu hỏi này",
                           placeholder="Ví dụ: Còn riêng Việt Nam thì sao? Hoặc: Số năm 2025 có chưa?")
        asked = st.form_submit_button("Hỏi tiếp", disabled=llm is None, type="primary")
    if asked and fq.strip():
        research_further(r, follow_question=fq)

    details = [("Số liệu khác định nghĩa, không so trực tiếp", b["definition_notes"]),
               ("Điều gì sẽ làm thay đổi kết luận", b["what_would_change"]),
               ("Câu bị bộ kiểm loại khỏi bản tóm tắt", b["guard_log"])]
    for title, items in details:
        if items:
            with st.expander(f"{title} ({len(items)})"):
                for x in items:
                    st.markdown(f"- {x}")

    st.divider()
    t1, t2, t3, t4 = st.tabs(["Nhận định đã kiểm", "Nhận định bị loại", "Nguồn", "Nhật ký chạy"])
    with t1:
        st.caption("Mở từng nhận định để xem câu trích và mở nguồn tại đúng chỗ. Đánh dấu nhận định sai rồi viết lại "
                   "bản tóm tắt.")
        excluded = set()
        for f in r["findings"]:
            status_txt = {"conflict": "mâu thuẫn", "agree": "khớp"}.get(f["status"], "một nguồn gốc")
            st.markdown(f"**{f['key']}. {f['label']}**: tin cậy {f['confidence']}, {status_txt}. "
                        f"{'; '.join(f['reasons'])}")
            for cid in f["claim_ids"]:
                c = claims[cid]
                s = sources[c["source_id"]]
                head = f"{cid}  {c['value_text']}  ({c['origin']}, hạng {c['tier']})" + ("  có cảnh báo" if c["flags"] else "")
                with st.expander(head):
                    st.write(c["claim_text"])
                    st.markdown(f'<blockquote class="src-quote">{h(c["quote"])}</blockquote>', unsafe_allow_html=True)
                    page = f", trang {c['page']}" if c.get("page") else ""
                    st.markdown(f"Nguồn: [{s['title'] or s['domain']}]({s['url']}){page}, đăng {s['published'] or 'không rõ'}. "
                                f"Giá trị chuẩn hóa: {fmt_value(c['value'], c['unit'])}. Kỳ: {c['period']}. "
                                f"Thị trường: {c['market']}. Phạm vi: {c['scope']}.")
                    link = evidence_url(s["url"], s["kind"], c["quote"], c.get("page"))
                    if link:
                        st.link_button("Mở nguồn tại câu trích" if s["kind"] != "pdf" else f"Mở PDF ở trang {c['page']}",
                                       link)
                    if c.get("context"):
                        ctx = h(c["context"]).replace(h(c["quote"]), f"<mark>{h(c['quote'])}</mark>", 1)
                        st.caption("Đoạn văn quanh câu trích, lấy nguyên từ nguồn:")
                        st.markdown(f'<div class="src-context">{ctx}</div>', unsafe_allow_html=True)
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
