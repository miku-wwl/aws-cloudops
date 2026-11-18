#!/usr/bin/env python3
"""pipeline：一次 CI 部署要过的四道控制 + 漂移的三条处理路线（第 16 讲实验 16-1，离线、零费用）。

    python pipeline.py scenarios.json

四道控制（顺序就是一个 apply 作业实际经历的顺序）：
  1 审批   GitHub 受保护环境：没批准，作业根本不开始，也拿不到 OIDC 令牌
  2 身份   STS 用角色信任策略比对令牌的 aud 与 sub（字面比较；新仓库的 sub 含数字 ID）
  3 权限   拿到临时凭证后，角色自己的策略决定能调哪些 API（含状态桶与 .tflock）
  4 锁     同一份状态同一时刻只允许一个写入者（S3 原生锁 <key>.tflock）
任何一道通过，都不代表其他几道也通过。
"""
from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path


def match(op: str, expected: str, actual: str) -> bool:
    return actual == expected if op == "StringEquals" else fnmatch.fnmatchcase(actual, expected)


def run(sc: dict) -> dict:
    job, role = sc["job"], sc["role"]
    if job.get("environment") and job["environment"].get("required_reviewers") and not job["environment"].get("approved"):
        return {"stage": "审批", "result": "作业等待审批（尚未请求令牌）"}
    tok = job["token"]
    if tok["aud"] != "sts.amazonaws.com":
        return {"stage": "身份", "result": "AssumeRoleWithWebIdentity 被拒：aud 不对"}
    if not match(role["sub_op"], role["sub"], tok["sub"]):
        return {"stage": "身份", "result": f"AssumeRoleWithWebIdentity 被拒：sub {tok['sub']} 不匹配"}
    missing = [a for a in job["needs"] if a not in role["allows"]]
    if missing:
        return {"stage": "权限", "result": f"拿到了凭证，但 {', '.join(missing)} 被拒（AccessDenied）"}
    if sc.get("lock_held_by"):
        return {"stage": "锁", "result": f"Error acquiring the state lock（持有者：{sc['lock_held_by']}）"}
    return {"stage": "通过", "result": "apply 可以开始——之后仍要独立验证结果"}


def drift_route(d: dict) -> str:
    if d.get("source") == "unknown" or not d.get("risk_understood", True):
        return "暂停：冻结写操作，保留状态、日志与现场，先调查来源与影响"
    if d.get("approved_change"):
        return "接受：把新值写进代码，走正常的 plan 与审批（不要让 apply 把紧急修复改回去）"
    return "恢复：审查一份只恢复这一处的 plan，再 apply 回到代码中的值"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenarios")
    a = ap.parse_args()
    spec = json.loads(Path(a.scenarios).read_text(encoding="utf-8"))
    for sc in spec["deploys"]:
        r = run(sc)
        print(f"  {sc['id']:3} [{r['stage']}] {sc['title']}\n       → {r['result']}")
    print()
    for d in spec["drifts"]:
        print(f"  {d['id']:3} {d['title']}\n       → {drift_route(d)}")


if __name__ == "__main__":
    main()
