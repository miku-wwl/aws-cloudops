#!/usr/bin/env python3
"""estimate：用真实单价估算一次实验的费用，并分清“销毁前”与“销毁后仍会计量”（第 19 讲实验 19-2）。

    python estimate.py prices.json scenario.json

费用 = 用量 × 单价，单位必须对齐：
  按小时计的（实例、公网 IPv4）：小时数 × 每小时单价
  按 GB·月计的（EBS 卷、快照、日志存储）：GB × 小时数 ÷ 730 × 每 GB·月单价（按 730 小时/月折算）
  按 GB 计的（日志写入）：GB × 每 GB 单价
"""
import json
import sys
from pathlib import Path

HOURS_PER_MONTH = 730


def cost(item, prices):
    p = prices[item["price"]]["usd"]
    unit = prices[item["price"]]["unit"]
    if unit in ("Hrs", "hour"):
        return p * item["hours"]
    if unit == "GB-Mo":
        return p * item["gb"] * item["hours"] / HOURS_PER_MONTH
    if unit == "GB":
        return p * item["gb"]
    raise ValueError(unit)


def main():
    prices = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sc = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    print(f"单价来源：{prices['source']}，{prices['region']}，{prices['date']}")
    print("  金额(美元)  单价          阶段    项目（用量）")
    totals = {}
    for it in sc["items"]:
        c = cost(it, prices["prices"])
        totals[it["phase"]] = totals.get(it["phase"], 0) + c
        pr = prices["prices"][it["price"]]
        print(f"  {c:>7.4f}  {pr['usd']:>7.4f}/{pr['unit']:5}  {it['phase']}  {it['name']}（{it['qty']}）")
    for ph, v in totals.items():
        print(f"  小计 {ph}：{v:.4f} 美元")
    print(f"  合计：{sum(totals.values()):.4f} 美元")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
