#!/usr/bin/env python3
"""opsim：用 IAM 策略模拟器核对“操作者最小权限策略”（第 10 讲实验 10-2）。

    python opsim.py            # 离线：对照已录制的 AWS 判定（aws_results.json）
    python opsim.py --live     # 在线：逐条调用 aws iam simulate-custom-policy 并重新录制

simulate-custom-policy 只做计算，不读写任何资源，也不收费；需要 iam:SimulateCustomPolicy 权限。
策略里的账户 ID 111122223333 是示例值——模拟器不检查资源是否存在，所以无需替换。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent


def simulate(policy: str, case: dict) -> str:
    cmd = ["aws", "iam", "simulate-custom-policy", "--output", "json",
           "--policy-input-list", policy, "--action-names", case["action"],
           "--resource-arns", case["resource"]]
    ctx = [{"ContextKeyName": k, "ContextKeyValues": [v], "ContextKeyType": "string"}
           for k, v in case["context"].items()]
    if ctx:
        cmd += ["--context-entries", json.dumps(ctx)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        return "error: " + (p.stderr.strip().splitlines() or ["?"])[-1][:120]
    r = json.loads(p.stdout)["EvaluationResults"][0]
    stmts = [s.get("SourcePolicyId", "") + ":" + str(s.get("StartPosition", {}).get("Line", "")) for s in r.get("MatchedStatements", [])]
    return r["EvalDecision"] + (f"  (matched {len(stmts)})" if stmts else "")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    policy = (HERE / "operator-policy.json").read_text(encoding="utf-8")
    cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))["cases"]
    store = HERE / "aws_results.json"
    recorded = json.loads(store.read_text(encoding="utf-8"))["results"] if store.exists() else {}
    fresh, bad = {}, 0
    for c in cases:
        got = simulate(policy, c) if a.live else recorded.get(c["id"], "未录制")
        fresh[c["id"]] = got
        ok = got.split()[0] == c["expect"]
        bad += 0 if ok else 1
        print(f"{c['id']:4} {c['action']:28} 预期={c['expect']:12} AWS={got.split()[0]:12} {'✓' if ok else '✗'}  {c['title']}")
    print(f"\n{len(cases)} 个用例，与手推结果不一致：{bad}")
    if a.live:
        store.write_text(json.dumps({"recorded": str(date.today()), "api": "iam:SimulateCustomPolicy", "results": fresh},
                                    ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"已录制到 {store.name}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
