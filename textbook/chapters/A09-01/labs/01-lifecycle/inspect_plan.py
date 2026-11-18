#!/usr/bin/env python3
"""inspect_plan：读 `terraform show -json <planfile>`，把每个资源的动作说清楚，并当作审批闸门（第 15 讲实验 15-1）。

    terraform show -json lab.tfplan > lab.plan.json
    python inspect_plan.py lab.plan.json                          # 列出变化
    python inspect_plan.py lab.plan.json --allow create,update    # 出现其他动作（delete / replace）就退出码 1
    python inspect_plan.py lab.plan.json --find "Example-Not"     # 计划文件里能不能找到某个明文

动作的读法（与 terraform plan 的符号对应）：
  create(+)  update(~)  delete(-)  replace(-/+ 或 +/-)  no-op（没有变化，但地址可能被 moved 改过）
  forget：removed 块让 Terraform 停止管理对象，但不销毁它
replace 时 action_reason 说明为什么要替换（例如 replace_by_triggers、replace_because_cannot_update）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def action_name(actions: list[str]) -> str:
    if actions in (["delete", "create"], ["create", "delete"]):
        return "replace"
    return "+".join(actions)


def changes(plan: dict) -> list[dict]:
    out = []
    for rc in plan.get("resource_changes", []):
        out.append({"address": rc["address"], "previous_address": rc.get("previous_address"),
                    "action": action_name(rc["change"]["actions"]), "reason": rc.get("action_reason")})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("planjson")
    ap.add_argument("--allow", help="允许的动作，逗号分隔，例如 create,update,no-op")
    ap.add_argument("--find", help="在计划 JSON 中搜索的明文")
    a = ap.parse_args()
    raw = Path(a.planjson).read_text(encoding="utf-8")
    plan = json.loads(raw)
    rows = changes(plan)
    for r in rows:
        moved = f"（由 {r['previous_address']} 移来）" if r["previous_address"] else ""
        why = f"  原因：{r['reason']}" if r["reason"] else ""
        print(f"  {r['action']:8} {r['address']}{moved}{why}")
    if not rows:
        print("  （没有资源变化）")
    status = 0
    if a.allow:
        allowed = set(a.allow.split(","))
        bad = [r for r in rows if r["action"] not in allowed]
        for r in bad:
            print(f"  ✗ 未获批准的动作：{r['action']} {r['address']}")
        status = 1 if bad else 0
        print("  闸门：" + ("拒绝" if bad else "通过"))
    if a.find:
        print(f"  计划 JSON 中{'包含' if a.find in raw else '不包含'}明文 “{a.find}”")
    sys.exit(status)


if __name__ == "__main__":
    main()
