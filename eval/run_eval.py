"""Run the live test cases and write eval/ket-qua-kiem-thu.md.

    python -m eval.run_eval            # all cases
    python -m eval.run_eval TC2 TC6    # some cases
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
LOAI = {"tot": "Làm tốt", "kho": "Khó, dữ liệu không rõ ràng", "thieu": "Thiếu dữ liệu",
        "that_bai": "Dự đoán chưa xử lý tốt"}


def _verified(r):
    return [c for c in r["claims"] if c["verified"]]


def check(r: dict, checks: dict) -> list[tuple[str, bool, str]]:
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
            res.append((name, b["decision"] in arg, f"khuyến nghị {b['decision']}"))
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
            g = [c for c in vc if c["metric"] == "growth" and c["value"] is not None and c["genre"]]
            top = max(g, key=lambda c: c["value"]) if g else None
            ok = bool(top) and arg in top["genre"].lower()
            res.append((name, ok, f"cao nhất: {top['genre']} {top['value_text']}" if top else "không có số tăng trưởng theo thể loại"))
    # always: every reason in the brief cites verified claims (the guard should guarantee it)
    ids = {c["id"] for c in vc}
    bad = [x for x in b["reasons"] if not set(x["claim_ids"]) <= ids]
    res.append(("ly_do_co_can_cu", not bad, "mọi lý do gắn nhận định đã kiểm" if not bad else f"{len(bad)} lý do sai"))
    return res


def summarize(r: dict, results) -> str:
    b, s = r["brief"], r["stats"]
    parts = [f"{b['decision']}, tin cậy {b['confidence']}.",
             f"Đọc {s['sources_read']} nguồn (lỗi {s['sources_failed']}), giữ {s['verified']}/{s['claims']} nhận định."]
    parts += [f"{'Đạt' if ok else 'Không đạt'} {name}: {msg}." for name, ok, msg in results]
    return " ".join(parts)


def main(ids: list[str]) -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252 when redirected
    cases = yaml.safe_load((HERE / "cases.yaml").read_text(encoding="utf-8"))
    if ids:
        cases = [c for c in cases if c["id"] in ids]
    OUT.mkdir(exist_ok=True)
    llm = LLM()
    rows = []
    for case in cases:
        print(f"== {case['id']}: {case['question']}")
        try:
            r = pipeline.run(case["question"], extra_urls=case.get("urls") or [], use_search=case.get("use_search", True),
                             llm=llm, progress=lambda m: print("  ", m))
        except Exception as e:
            rows.append((case, None, [("chay", False, f"lỗi: {e}")]))
            print("   LỖI", e)
            continue
        (OUT / f"{case['id']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        (OUT / f"{case['id']}.md").write_text(brief_markdown(r), encoding="utf-8")
        res = check(r, case.get("checks", {}))
        rows.append((case, r, res))
        print("  ", "ĐẠT" if all(ok for _, ok, _ in res) else "CHƯA ĐẠT", summarize(r, res))

    md = ["# Kết quả kiểm thử", "",
          "Bảng do `python -m eval.run_eval` sinh ra. Chi tiết từng lần chạy nằm trong `eval/results/`.", "",
          "| Mã | Loại | Câu hỏi | Kỳ vọng | Kết quả thực tế | Đạt/Chưa đạt | Điều học được |",
          "|---|---|---|---|---|---|---|"]
    for case, r, res in rows:
        actual = summarize(r, res) if r else res[0][2]
        ok = "Đạt" if all(o for _, o, _ in res) else "Chưa đạt"
        cells = [case["id"], LOAI.get(case["loai"], case["loai"]), case["question"], case["ky_vong"], actual, ok,
                 case.get("hoc_duoc") or ""]
        md.append("| " + " | ".join(str(x).replace("|", "/").replace("\n", " ") for x in cells) + " |")
    name = "ket-qua-kiem-thu.md" if not ids else f"ket-qua-{'-'.join(ids)}.md"
    (HERE / name).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Đã ghi eval/{name}")


if __name__ == "__main__":
    main(sys.argv[1:])
