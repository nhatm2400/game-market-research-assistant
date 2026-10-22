"""Run the live test cases and write eval/ket-qua-kiem-thu.md.

    python -m eval.run_eval            # all cases
    python -m eval.run_eval TC2 TC6    # some cases
    python -m eval.run_eval --report   # rebuild the table from eval/results/*.json, no LLM calls
    python -m eval.run_eval --compare  # M2 (eval/results_m2) vs M3 (eval/results) -> eval/so-sanh-m2-m3.md
    python -m eval.run_eval --rescore  # apply the current code rules to the stored live runs, no LLM calls

`checks` are the Mission 2 conditions, kept unchanged as the regression test. `checks_m3` are the
conditions added for Mission 3. A case with `parent` and `follow_up` asks a follow-up question on
the parent case's result, to test that research can go on without losing context.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

from core import pipeline  # noqa: E402
from core.llm import LLM  # noqa: E402
from core.periods import parse_period  # noqa: E402
from core.report import brief_markdown  # noqa: E402
from core.textnorm import normalize, number_tokens  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
OUT_M2 = HERE / "results_m2"
LOAI = {"tot": "Làm tốt", "kho": "Khó, dữ liệu không rõ ràng", "thieu": "Thiếu dữ liệu",
        "that_bai": "Dự đoán chưa xử lý tốt", "tiep": "Nghiên cứu tiếp, giữ bối cảnh",
        "cu": "Nguồn cũ, số dự báo"}


def _verified(r):
    return [c for c in r["claims"] if c["verified"]]


def _bucket_tokens(r: dict, bucket: str) -> set[str]:
    claims = {c["id"]: c for c in r["claims"]}
    return {t for x in r["brief"].get(bucket, []) for cid in x["claim_ids"] for t in number_tokens(claims[cid]["value_text"])}


def _top_growth(vc: list[dict], market: str | None = None):
    g = [c for c in vc if c["metric"] == "growth" and c["value"] is not None and c["genre"]
         and (market is None or c["market"] == market)]
    return max(g, key=lambda c: c["value"]) if g else None


def check(r: dict, checks: dict, parent: dict | None = None, always: bool = True) -> list[tuple[str, bool, str]]:
    res = []
    vc = _verified(r)
    b = r["brief"]
    for name, arg in checks.items():
        if name == "verified_numbers":
            toks = {t for c in vc for t in number_tokens(c["value_text"])}
            miss = [n for n in arg if normalize(n) not in toks]
            res.append((name, not miss, f"thiếu {miss}" if miss else f"có đủ {arg}"))
        elif name == "origin_includes":
            origins = sorted({c["origin"] for c in vc})
            res.append((name, arg in origins, f"nguồn gốc: {origins}"))
        elif name == "has_conflict":
            res.append((name, bool(b["conflicts"]) == arg, f"{len(b['conflicts'])} mâu thuẫn"))
        elif name == "confidence_not":
            res.append((name, b["confidence"] not in arg, f"tin cậy {b['confidence']}"))
        elif name == "decision_in":
            res.append((name, b["decision"] in arg, f"kết luận {b['decision']}"))
        elif name == "flag_any":
            flags = [f for c in vc for f in c["flags"]]
            hit = [a for a in arg if any(a in f for f in flags)]
            res.append((name, bool(hit), f"cảnh báo khớp: {hit}" if hit else "không có cảnh báo nào khớp"))
        elif name == "min_reasons":
            res.append((name, len(b["reasons"]) >= arg, f"{len(b['reasons'])} lý do"))
        elif name == "min_distinct_tiers":
            tiers = sorted({s["tier"] for s in r["sources"] if not s["error"]})
            res.append((name, len(tiers) >= arg, f"hạng nguồn: {tiers}"))
        elif name == "no_verified_number_for_period":
            bad = [c["id"] for c in vc if (sp := parse_period(c["period"])) and f"{sp.start:%Y-%m}" == arg]
            res.append((name, not bad, f"nhận định có kỳ {arg}: {bad}" if bad else f"không có số nào cho kỳ {arg}"))
        elif name == "top_growth_genre":
            top = _top_growth(vc)
            ok = bool(top) and arg in top["genre"].lower()
            res.append((name, ok, f"cao nhất: {top['genre']} {top['value_text']}" if top else "không có số tăng trưởng theo thể loại"))
        # ---- Mission 3 ----
        elif name == "top_growth_genre_in_market":      # the M2 check above also counted other countries
            top = _top_growth(vc, r["question_market"])
            ok = bool(top) and arg in top["genre"].lower()
            res.append((name, ok, f"cao nhất ở {r['question_market']}: {top['genre']} {top['value_text']}" if top
                        else f"không có số tăng trưởng theo thể loại của {r['question_market']}"))
        elif name in ("trusted_includes_numbers", "uncertain_includes_numbers"):
            bucket = name.split("_")[0]
            toks = _bucket_tokens(r, bucket)
            miss = [n for n in arg if normalize(n) not in toks]
            label = "có thể tin" if bucket == "trusted" else "chưa chắc chắn"
            res.append((name, not miss, f"mục {label} thiếu {miss}" if miss else f"mục {label} có {arg}"))
        elif name == "trusted_excludes_numbers":
            bad = [n for n in arg if normalize(n) in _bucket_tokens(r, "trusted")]
            res.append((name, not bad, f"mục có thể tin chứa {bad}" if bad else f"{arg} không nằm trong mục có thể tin"))
        elif name == "uncertain_reason_any":
            whys = [w for x in b.get("uncertain", []) for w in x["why"]]
            hit = [a for a in arg if any(a in w for w in whys)]
            res.append((name, bool(hit), f"lý do chưa chắc chắn khớp: {hit}" if hit else "không có lý do nào khớp"))
        elif name == "next_steps_min":
            n = len(b.get("next_steps", []))
            res.append((name, n >= arg, f"{n} bước tìm hiểu tiếp"))
        elif name == "chart_step":
            hit = [s for s in b.get("next_steps", []) if s["url"] and "chỉ có con số" in s["text"]]
            res.append((name, bool(hit) == arg, f"có bước mở biểu đồ: {hit[0]['url']}" if hit
                        else "không có bước chỉ tới biểu đồ chưa đọc được"))
        elif name == "window_label":
            res.append((name, r["window"]["label"] == arg, f"khung thời gian: {r['window']['label']}"))
        elif name == "summary_not_empty":
            res.append((name, bool(b["summary"].strip()), "có câu tóm tắt" if b["summary"].strip() else "tóm tắt rỗng"))
        elif name == "question_market":
            res.append((name, r["question_market"] == arg, f"thị trường của câu hỏi đầy đủ: {r['question_market']}"))
        elif name == "context_kept":
            if parent is None:
                res.append((name, False, "không có kết quả của case gốc"))
                continue
            now = {c["id"]: c for c in r["claims"]}
            lost = [c["id"] for c in _verified(parent) if not now.get(c["id"], {}).get("verified")]
            res.append((name, not lost and r.get("parent_id") == parent["id"],
                        f"giữ {len(_verified(parent)) - len(lost)}/{len(_verified(parent))} nhận định của câu hỏi trước"))
        elif name == "llm_calls_max":
            n = r["stats"]["llm_calls"]
            res.append((name, n <= arg, f"{n} lượt gọi LLM"))
    if always:
        # every reason in the brief cites verified claims (the guard should guarantee it)
        ids = {c["id"] for c in vc}
        bad = [x for x in b["reasons"] if not set(x["claim_ids"]) <= ids]
        res.append(("ly_do_co_can_cu", not bad, "mọi lý do gắn nhận định đã kiểm" if not bad else f"{len(bad)} lý do sai"))
    return res


def summarize(r: dict, results) -> str:
    b, s = r["brief"], r["stats"]
    parts = []
    if r.get("asked"):
        parts.append(f"Hỏi tiếp \"{r['asked']}\", câu hỏi đầy đủ: \"{r['question']}\"; giữ {s.get('carried', 0)} nhận định.")
    parts += [f"{b['decision']}, tin cậy {b['confidence']}.",
              f"Đọc {s['sources_read']} nguồn (lỗi {s['sources_failed']}), giữ {s['verified']}/{s['claims']} nhận định."]
    if "trusted" in b:
        parts.append(f"Có thể tin {len(b['trusted'])}, chưa chắc chắn {len(b['uncertain'])}, ngoài phạm vi "
                     f"{len(b.get('other', []))}, {len(b['next_steps'])} bước tìm hiểu tiếp.")
    parts += [f"{'Đạt' if ok else 'Không đạt'} {name}: {msg}." for name, ok, msg in results]
    return " ".join(parts)


def _load(folder: Path, cid: str) -> dict | None:
    f = folder / f"{cid}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def run_case(case: dict, llm: LLM, done: dict) -> tuple[dict, dict | None]:
    progress = lambda m: print("  ", m)  # noqa: E731
    if case.get("parent"):
        parent = done.get(case["parent"]) or _load(OUT, case["parent"])
        if parent is None:
            raise RuntimeError(f"chưa có kết quả của {case['parent']}")
        return pipeline.follow_up(parent, case["follow_up"], extra_urls=case.get("urls") or [],
                                  use_search=case.get("use_search", True), llm=llm, progress=progress), parent
    return pipeline.run(case["question"], extra_urls=case.get("urls") or [], use_search=case.get("use_search", True),
                        llm=llm, progress=progress), None


def all_checks(r: dict, case: dict, parent: dict | None) -> list:
    return check(r, case.get("checks", {}), parent) + [(f"[M3] {n}", ok, m) for n, ok, m in
                                                       check(r, case.get("checks_m3", {}), parent, always=False)]


def compare(cases: list[dict]) -> None:
    """Same checks on the M2 results and the M3 results, side by side."""
    def stat(r, case, key):
        if r is None:
            return None
        parent = _load(OUT_M2 if r.get("_m2") else OUT, case["parent"]) if case.get("parent") else None
        res = check(r, case.get(key, {}), parent, always=key == "checks")
        return sum(ok for _, ok, _ in res), len(res)

    def fmt(x):
        return "chưa có" if x is None else f"{x[0]}/{x[1]}"

    rows, tot = [], {"m2_old": [0, 0], "m3_old": [0, 0], "m2_new": [0, 0], "m3_new": [0, 0]}
    for case in cases:
        m2, m3 = _load(OUT_M2, case["id"]), _load(OUT, case["id"])
        if m2:
            m2["_m2"] = True
        cells = {k: stat(r, case, chk) for k, r, chk in
                 (("m2_old", m2, "checks"), ("m3_old", m3, "checks"), ("m2_new", m2, "checks_m3"), ("m3_new", m3, "checks_m3"))}
        for k, v in cells.items():
            if v and v[1]:
                tot[k][0] += v[0]
                tot[k][1] += v[1]
        b2, b3 = (m2 or {}).get("brief", {}), (m3 or {}).get("brief", {})
        dec = f"{b2.get('decision', '-')} / {b2.get('confidence', '-')} → {b3.get('decision', '-')} / {b3.get('confidence', '-')}"
        buckets = (f"{len(b3['trusted'])} / {len(b3['uncertain'])} / {len(b3.get('other', []))} / {len(b3['next_steps'])}"
                   if "trusted" in b3 else "-")
        empty = lambda b: "rỗng" if b and not b.get("summary", "").strip() else ("có" if b else "-")  # noqa: E731
        rows.append(f"| {case['id']} | {LOAI.get(case['loai'], case['loai'])} | {fmt(cells['m2_old'])} → {fmt(cells['m3_old'])} "
                    f"| {fmt(cells['m2_new'])} → {fmt(cells['m3_new'])} | {dec} | {empty(b2)} → {empty(b3)} | {buckets} |")
    md = ["# So sánh Mission 2 và Mission 3", "",
          "Bảng do `python -m eval.run_eval --compare` sinh ra: cùng một bộ điều kiện chấm được áp lên kết quả chạy thật",
          "của phiên bản M2 (`eval/results_m2/`) và M3 (`eval/results/`). \"Điều kiện M2\" là các điều kiện cũ, giữ nguyên để",
          "kiểm regression. \"Điều kiện M3\" là các điều kiện mới cho yêu cầu cải tiến; M2 không có các tính năng này nên",
          "không đạt là đúng. Cột cuối chỉ có ở M3: số mục có thể tin / chưa chắc chắn / ngoài phạm vi / bước tìm hiểu tiếp.", "",
          "| Mã | Loại | Điều kiện M2: M2 → M3 | Điều kiện M3: M2 → M3 | Kết luận / tin cậy: M2 → M3 | Tóm tắt | M3: tin / chưa chắc / ngoài / bước |",
          "|---|---|---|---|---|---|---|"] + rows
    md += ["", f"Tổng điều kiện M2 đạt: M2 {tot['m2_old'][0]}/{tot['m2_old'][1]}, M3 {tot['m3_old'][0]}/{tot['m3_old'][1]}. "
               f"Tổng điều kiện M3 đạt: M2 {tot['m2_new'][0]}/{tot['m2_new'][1]}, M3 {tot['m3_new'][0]}/{tot['m3_new'][1]}."]
    (HERE / "so-sanh-m2-m3.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("Đã ghi eval/so-sanh-m2-m3.md")


def main(ids: list[str]) -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252 when redirected
    flags = {i for i in ids if i.startswith("--")}
    ids = [i for i in ids if not i.startswith("--")]
    cases = yaml.safe_load((HERE / "cases.yaml").read_text(encoding="utf-8"))
    if "--compare" in flags:
        return compare(cases)
    if ids:
        cases = [c for c in cases if c["id"] in ids]
    OUT.mkdir(exist_ok=True)
    rows, done = [], {}
    llm = None if flags & {"--report", "--rescore"} else LLM()
    for case in cases:
        if llm is None:
            r = _load(OUT, case["id"])
            if r is None:
                rows.append((case, None, [("chay", False, "chưa có kết quả trong eval/results")]))
                continue
            if "--rescore" in flags:
                r = pipeline.rescore(r)
                (OUT / f"{case['id']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
                (OUT / f"{case['id']}.md").write_text(brief_markdown(r), encoding="utf-8")
            parent = _load(OUT, case["parent"]) if case.get("parent") else None
            rows.append((case, r, all_checks(r, case, parent)))
            continue
        print(f"== {case['id']}: {case['question']}")
        try:
            r, parent = run_case(case, llm, done)
        except Exception as e:
            rows.append((case, None, [("chay", False, f"lỗi: {e}")]))
            print("   LỖI", e)
            continue
        done[case["id"]] = r
        (OUT / f"{case['id']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        (OUT / f"{case['id']}.md").write_text(brief_markdown(r), encoding="utf-8")
        res = all_checks(r, case, parent)
        rows.append((case, r, res))
        print("  ", "ĐẠT" if all(ok for _, ok, _ in res) else "CHƯA ĐẠT", summarize(r, res))

    md = ["# Kết quả kiểm thử", "",
          "Bảng do `python -m eval.run_eval` sinh ra. Chi tiết từng lần chạy nằm trong `eval/results/`. Điều kiện có",
          "nhãn [M3] là điều kiện mới của Mission 3; các điều kiện còn lại giữ nguyên từ Mission 2 để kiểm regression.", "",
          "| Mã | Loại | Câu hỏi | Kỳ vọng | Kết quả thực tế | Đạt/Chưa đạt | Điều học được |",
          "|---|---|---|---|---|---|---|"]
    for case, r, res in rows:
        actual = summarize(r, res) if r else res[0][2]
        ok = "Đạt" if all(o for _, o, _ in res) else "Chưa đạt"
        q = case["question"] + (f" → hỏi tiếp: \"{case['follow_up']}\"" if case.get("follow_up") else "")
        cells = [case["id"], LOAI.get(case["loai"], case["loai"]), q, case["ky_vong"], actual, ok,
                 case.get("hoc_duoc") or ""]
        md.append("| " + " | ".join(str(x).replace("|", "/").replace("\n", " ") for x in cells) + " |")
    name = "ket-qua-kiem-thu.md" if not ids else f"ket-qua-{'-'.join(ids)}.md"
    (HERE / name).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Đã ghi eval/{name}")


if __name__ == "__main__":
    main(sys.argv[1:])
