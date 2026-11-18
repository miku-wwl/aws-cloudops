#!/usr/bin/env python3
"""canon：把 DynamoDB 条目规范化后算 SHA-256，用来比较“恢复表”与“恢复点时刻的基线”（实验 13-1）。

    python canon.py baseline.json restored.json      # 两份 scan 输出（DynamoDB JSON）逐项比较
    aws dynamodb scan --table-name T --consistent-read --output json > restored.json

规范化规则（缺一条，哈希就可能“假不一致”）：
  1. 按主键（pk, sk）排序——scan 的返回顺序不保证稳定；
  2. 每个条目的属性按名称排序；
  3. 数字（N）按数值比较：DynamoDB 以字符串传输数字，"100" 与 "100.0" 是同一个数；
  4. 集合类型（SS / NS）排序；字符串、布尔、空值原样保留。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path


def plain(v: dict):
    (t, x), = v.items()
    if t == "N":
        d = Decimal(x).normalize()
        return {"N": format(d, "f") if d == d.to_integral() else str(d)}
    if t in ("SS", "NS"):
        return {t: sorted(x if t == "SS" else [plain({"N": n})["N"] for n in x])}
    if t == "L":
        return {"L": [plain(i) for i in x]}
    if t == "M":
        return {"M": {k: plain(x[k]) for k in sorted(x)}}
    return {t: x}


def canonical(items: list[dict]) -> list[str]:
    rows = [{k: plain(it[k]) for k in sorted(it)} for it in items]
    rows.sort(key=lambda r: (r["pk"]["S"], r["sk"]["S"]))
    return [json.dumps(r, ensure_ascii=False, separators=(",", ":"), sort_keys=True) for r in rows]


def digest(items: list[dict]) -> str:
    return hashlib.sha256("\n".join(canonical(items)).encode("utf-8")).hexdigest()


def summary(items: list[dict]) -> dict:
    return {"count": len(items), "amount_sum": sum(Decimal(i["amount"]["N"]) for i in items if "amount" in i),
            "keys": sorted(i["sk"]["S"] for i in items), "sha256": digest(items)}


def load(path: str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["Items"] if isinstance(data, dict) else data


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("baseline")
    ap.add_argument("restored")
    a = ap.parse_args()
    b, r = summary(load(a.baseline)), summary(load(a.restored))
    amount = lambda d: format(d.normalize(), "f")
    print(f"  行数      基线 {b['count']:<6} 恢复 {r['count']:<6} {'✓' if b['count'] == r['count'] else '✗'}")
    print(f"  金额合计  基线 {amount(b['amount_sum']):<6} 恢复 {amount(r['amount_sum']):<6} "
          f"{'✓' if b['amount_sum'] == r['amount_sum'] else '✗'}")
    extra, missing = sorted(set(r["keys"]) - set(b["keys"])), sorted(set(b["keys"]) - set(r["keys"]))
    print(f"  多出 {extra or '无'}；缺少 {missing or '无'}")
    print(f"  SHA-256   基线 {b['sha256'][:16]}…  恢复 {r['sha256'][:16]}…  {'✓' if b['sha256'] == r['sha256'] else '✗'}")
    ok = b == r
    print("  结论：", "恢复表与恢复点时刻的基线一致" if ok else "不一致——先确认比较的是不是同一个恢复点")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
