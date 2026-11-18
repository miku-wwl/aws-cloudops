#!/usr/bin/env python3
"""ir：事故分析的两件基本功（第 14 讲实验 14-1，离线、零费用）。

    python ir.py dx case.json          # 鉴别诊断：用观察去“证伪”假设，剩下的才是候选根因
    python ir.py window probes.jsonl   # 由探针记录推出停机时长的上下界，以及检测与恢复耗时

鉴别诊断的规则：每个假设对每条观察给出预测（"+" 应该看到、"-" 不应该看到、"0" 无关）。
  观察与预测矛盾 → 该假设被证伪；与所有观察都不矛盾、且至少被一条观察正面支持 → 存活。
  多个假设存活 = 证据不足，要设计新的观察去区分它们，而不是挑一个最顺眼的写进报告。
时间窗的规则：探针每隔 Δ 观测一次，真实的中断起点落在“最后一次成功”与“第一次失败”之间，
  终点落在“最后一次失败”与“第一次恢复成功”之间——所以停机时长只能给出区间，不是一个数。
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def dx(case: dict) -> list[dict]:
    seen = {o["id"]: o["value"] for o in case["observations"]}
    out = []
    for h in case["hypotheses"]:
        contra, support, missing = [], [], []
        for oid, pred in h["predicts"].items():
            if oid not in seen:
                missing.append(oid)
            elif pred == "0":
                continue
            elif (pred == "+") == bool(seen[oid]):
                support.append(oid)
            else:
                contra.append(oid)
        verdict = "证伪" if contra else ("存活" if support else "无法判断")
        out.append({"id": h["id"], "title": h["title"], "verdict": verdict,
                    "contradicted_by": contra, "supported_by": support, "missing": missing})
    return out


def parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def window(probes: list[dict], alert: str | None = None) -> dict:
    probes = sorted(probes, key=lambda p: p["ts"])
    fails = [i for i, p in enumerate(probes) if not p["ok"]]
    if not fails:
        return {"outage": False}
    f0, f1 = fails[0], fails[-1]
    last_ok = probes[f0 - 1]["ts"] if f0 > 0 else None
    first_ok = probes[f1 + 1]["ts"] if f1 + 1 < len(probes) else None
    lo = (parse(probes[f1]["ts"]) - parse(probes[f0]["ts"])).total_seconds() / 60
    hi = ((parse(first_ok) - parse(last_ok)).total_seconds() / 60) if last_ok and first_ok else None
    res = {"outage": True, "last_ok": last_ok, "first_fail": probes[f0]["ts"], "last_fail": probes[f1]["ts"],
           "first_ok_after": first_ok, "duration_min_lower": lo, "duration_min_upper": hi}
    if alert:
        res["detect_min"] = (parse(alert) - parse(probes[f0]["ts"])).total_seconds() / 60
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["dx", "window"])
    ap.add_argument("file")
    ap.add_argument("--alert", help="第一条告警的 UTC 时间（可选）")
    a = ap.parse_args()
    if a.what == "dx":
        for r in dx(json.loads(Path(a.file).read_text(encoding="utf-8"))):
            why = (f"被 {','.join(r['contradicted_by'])} 证伪" if r["contradicted_by"]
                   else f"得到 {','.join(r['supported_by'])} 支持")
            gap = f"；尚缺 {','.join(r['missing'])}" if r["missing"] else ""
            print(f"  {r['id']}  {r['verdict']:4}  {r['title']}（{why}{gap}）")
    else:
        probes = [json.loads(l) for l in Path(a.file).read_text(encoding="utf-8").splitlines() if l.strip()]
        w = window(probes, a.alert)
        for k, v in w.items():
            print(f"  {k:20} {v}")


if __name__ == "__main__":
    main()
