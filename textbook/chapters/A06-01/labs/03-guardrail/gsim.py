#!/usr/bin/env python3
"""gsim：用 IAM 策略模拟器验证“保护 Owner 标签”的护栏（第 11 讲实验 11-3）。

    python gsim.py            # 离线：对照录制结果
    python gsim.py --live     # 在线：调用 aws iam simulate-custom-policy（只做计算、不收费）

同一份策略语言既可写成 IAM 策略，也可写成组织的 SCP；本书账户不在 AWS Organizations 中，
所以用模拟器验证策略逻辑本身。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent


def simulate(policy: str, resource: str, case: dict) -> str:
    cmd = ["aws", "iam", "simulate-custom-policy", "--output", "json", "--policy-input-list", policy,
           "--action-names", case["action"], "--resource-arns", resource]
    ctx = [{"ContextKeyName": k, "ContextKeyValues": v, "ContextKeyType": "stringList"} for k, v in case["context"].items()]
    if ctx:
        cmd += ["--context-entries", json.dumps(ctx)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        return "error: " + (p.stderr.strip().splitlines() or ["?"])[-1][:100]
    return json.loads(p.stdout)["EvaluationResults"][0]["EvalDecision"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    policy = (HERE / "protect-owner-tag.json").read_text(encoding="utf-8")
    spec = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    store = HERE / "aws_results.json"
    recorded = json.loads(store.read_text(encoding="utf-8"))["results"] if store.exists() else {}
    fresh, bad = {}, 0
    for c in spec["cases"]:
        got = simulate(policy, spec["resource"], c) if a.live else recorded.get(c["id"], "未录制")
        fresh[c["id"]] = got
        bad += got != c["expect"]
        ctx = ",".join(c["context"].get("aws:TagKeys", [])) or "-"
        print(f"{c['id']}  {c['action']:20} TagKeys={ctx:18} 预期={c['expect']:12} AWS={got:12} {'✓' if got == c['expect'] else '✗'}")
    print(f"\n{len(spec['cases'])} 个用例，不一致：{bad}")
    if a.live:
        store.write_text(json.dumps({"recorded": str(date.today()), "api": "iam:SimulateCustomPolicy", "results": fresh},
                                    ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
