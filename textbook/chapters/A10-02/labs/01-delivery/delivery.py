#!/usr/bin/env python3
"""delivery：一个新账户能不能交付？按证据逐级判定（第 18 讲实验 18-1，离线、零费用）。

    python delivery.py cases.json          # 跑全部案例
    python delivery.py cases.json C5 -v    # 只看一个案例的逐级结果

八个关口按顺序检查，输出第一个“挡住交付”的关口：
  1 账户存在         Organizations 里有这个账户 ID
  2 OU 已注册        目标 OU 已启用 AWSControlTowerBaseline 且状态成功
  3 账户已纳管       Control Tower 中账户为 ENROLLED
  4 AFT 开户         仅当账户来自 AFT：Provisioning 成功
  5 AFT 框架         仅当账户来自 AFT：Framework 成功
  6 全局定制         仅当账户来自 AFT
  7 账户定制         仅当账户来自 AFT
  8 独立验收         每一条业务验收项都要有“真实送达”的证据

每个关口的结论只有五种：
  PASS     证据表明通过
  FAIL     证据表明失败（或“必需”的阶段没有运行）——挡住交付
  MISSING  “必需”的阶段没有证据（UNKNOWN / 缺字段）——挡住交付，但不能说它失败了
  SKIP     不需要且没有运行，或这条路径不适用（例如不是 AFT 开户）
  WARN     不需要的阶段失败了：不挡交付，但流水线需要修
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

OK = {"SUCCEEDED", "SUCCESS", "ENROLLED", "ENABLED"}


def stage(name, status, required=True, applicable=True):
    if not applicable:
        return name, "SKIP", "不适用"
    s = (status or "UNKNOWN").upper()
    if s in OK:
        return name, "PASS", s
    if s == "NOT_RUN":
        return (name, "FAIL", "必需却未运行") if required else (name, "SKIP", "不需要，未运行")
    if s == "UNKNOWN":
        return (name, "MISSING", "没有证据") if required else (name, "SKIP", "不需要，状态未知")
    return (name, "FAIL", s) if required else (name, "WARN", f"{s}（不需要，不挡交付）")


def evaluate(case: dict) -> dict:
    a, ou, aft = case.get("account", {}), case.get("ou", {}), case.get("aft", {})
    via_aft = a.get("path") == "aft"
    checks = [
        ("账户存在", "PASS", a.get("id", "")) if a.get("exists") else ("账户存在", "FAIL", "Organizations 中找不到"),
        stage("OU 已注册", ou.get("baseline")),
        stage("账户已纳管", case.get("enrollment")),
        stage("AFT 开户", aft.get("provisioning"), applicable=via_aft),
        stage("AFT 框架", aft.get("framework"), applicable=via_aft),
        stage("全局定制", aft.get("global", {}).get("status"), aft.get("global", {}).get("required", False), via_aft),
        stage("账户定制", aft.get("account", {}).get("status"), aft.get("account", {}).get("required", False), via_aft),
    ]
    acc = case.get("acceptance", {})
    if not acc:
        checks.append(("独立验收", "MISSING", "没有定义验收项"))
    else:
        bad = [k for k, v in acc.items() if v is False]
        unknown = [k for k, v in acc.items() if v is None]
        if bad:
            checks.append(("独立验收", "FAIL", "未达成：" + "、".join(bad)))
        elif unknown:
            checks.append(("独立验收", "MISSING", "缺证据：" + "、".join(unknown)))
        else:
            checks.append(("独立验收", "PASS", "全部有送达证据"))
    first = next((c for c in checks if c[1] in ("FAIL", "MISSING")), None)
    if first is None:
        verdict = "可交付" + ("（有 WARN）" if any(c[1] == "WARN" for c in checks) else "")
    elif first[1] == "FAIL":
        verdict = f"阻塞于「{first[0]}」"
    else:
        verdict = f"证据不足于「{first[0]}」"
    return {"checks": checks, "verdict": verdict, "first": first}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cases")
    ap.add_argument("only", nargs="?")
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    spec = json.loads(Path(a.cases).read_text(encoding="utf-8"))
    for c in spec["cases"]:
        if a.only and c["id"] != a.only:
            continue
        r = evaluate(c)
        print(f"{c['id']:3} {c['title']}\n      → {r['verdict']}" + (f"：{r['first'][2]}" if r["first"] else ""))
        if a.v:
            for name, res, why in r["checks"]:
                print(f"        {res:7} {name}  {why}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
