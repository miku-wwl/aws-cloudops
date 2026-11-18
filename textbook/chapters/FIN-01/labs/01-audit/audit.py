#!/usr/bin/env python3
"""audit：Destroy 之后的账单行，到底是哪一种“增长”？（第 19 讲实验 19-1，离线、零费用）

    python audit.py cases/F1-demo.json
    python audit.py cases/*.json --brief

输入是一次实验的证据快照：销毁时刻、实时盘点（含覆盖范围）、以及若干账单行。
账单行字段沿用 CUR 2.0 / Data Exports 的含义：
  line_item_usage_start_date / _end_date   用量发生的时间段（UTC）
  line_item_line_item_type                 Usage / Credit / Refund / Tax …
  line_item_resource_id、product_region    资源与区域
  observed                                 你第一次在账单里看到它的时间（入账时间的近似）

每一行只会落入一类：
  PRE_DESTROY       用量在销毁前就结束了；销毁后才出现在账单里也只是“晚入账”
  RETAINED          销毁后仍在计量，但资源在盘点中，且有批准的保留期限
  RESIDUAL          销毁后仍在计量，资源在盘点中，但没有批准 → 要处置
  UNEXPLAINED       销毁后仍在计量，盘点覆盖完整却找不到资源 → 查别的 State / 账户
  COVERAGE_GAP      销毁后仍在计量，资源所在区域或服务不在盘点覆盖范围内 → 先补盘点
  ADJUSTMENT        Credit / Refund 等调整项，不是用量
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

USAGE_TYPES = {"Usage", "DiscountedUsage", "SavingsPlanCoveredUsage"}


def t(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def classify(line: dict, case: dict) -> tuple[str, str]:
    if line["line_item_line_item_type"] not in USAGE_TYPES:
        return "ADJUSTMENT", f"{line['line_item_line_item_type']} {line['cost']:+.4f}"
    destroy = t(case["destroy_utc"])
    if t(line["line_item_usage_end_date"]) <= destroy:
        late = t(line["observed"]) > destroy
        return "PRE_DESTROY", "销毁前的用量" + ("，销毁后才入账" if late else "")
    cov = case["coverage"]
    region, service = line["product_region"], line["service"]
    if region not in cov["regions"] or service not in cov["services"]:
        return "COVERAGE_GAP", f"{region}/{service} 不在盘点范围内"
    inv = {r["id"]: r for r in case["inventory"]}
    r = inv.get(line["line_item_resource_id"])
    if r is None:
        return "UNEXPLAINED", f"盘点中找不到 {line['line_item_resource_id']}"
    if r.get("retain_until") and r.get("approved_by"):
        return "RETAINED", f"批准保留至 {r['retain_until']}（{r['approved_by']}）"
    return "RESIDUAL", f"{r['id']} 仍存在且未获批准保留"


def verdict(classes: list[str]) -> str:
    if "COVERAGE_GAP" in classes:
        return "盘点覆盖不足：不能宣称已清理"
    if "RESIDUAL" in classes:
        return "发现未批准的残留：按归属与审批处置"
    if "UNEXPLAINED" in classes:
        return "销毁后有无法解释的用量：查其他 State / 账户"
    return "已清理（保留项均获批准）：等旧用量入账后复核"


def audit(case: dict) -> dict:
    rows = []
    for ln in case["lines"]:
        cls, why = classify(ln, case)
        rows.append((ln, cls, why))
    pre = sum(ln["cost"] for ln, c, _ in rows if c == "PRE_DESTROY")
    post = sum(ln["cost"] for ln, c, _ in rows if c in ("RETAINED", "RESIDUAL", "UNEXPLAINED", "COVERAGE_GAP"))
    return {"rows": rows, "pre": pre, "post": post, "verdict": verdict([c for _, c, _ in rows])}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cases", nargs="+")
    ap.add_argument("--brief", action="store_true")
    a = ap.parse_args()
    for path in a.cases:
        case = json.loads(Path(path).read_text(encoding="utf-8"))
        r = audit(case)
        print(f"== {case['id']} {case['title']}")
        if not a.brief:
            for ln, cls, why in r["rows"]:
                print(f"   {cls:12} {ln['usage_type']:24} {ln['cost']:>8.4f}  {why}")
            print(f"   销毁前用量 {r['pre']:.4f} 美元 · 销毁后仍在计量 {r['post']:.4f} 美元")
        print(f"   结论：{r['verdict']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
