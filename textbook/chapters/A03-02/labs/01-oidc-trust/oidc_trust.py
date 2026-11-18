#!/usr/bin/env python3
"""oidc_trust：GitHub Actions OIDC 令牌 × 角色信任策略的匹配矩阵（第 07 讲实验 7-1）。

    python oidc_trust.py                  # 本地：每个令牌能否扮演每个角色
    python oidc_trust.py --aws            # 另用 IAM Access Analyzer validate-policy 校验每份信任策略（免费）

令牌声明（claims）来自 GitHub 文档的格式：
  旧格式 sub：repo:<owner>/<repo>:ref:refs/heads/<branch>
  新格式 sub：repo:<owner>@<ownerId>/<repo>@<repoId>:ref:refs/heads/<branch>
      （2026-07-15 之后创建、改名或转移的仓库默认使用；旧仓库可在 OIDC 设置中选择启用）
IAM 对 GitHub 这类“共享 OIDC 提供商”要求信任策略必须评估 sub（或 job_workflow_ref），
且不能只是通配符，否则创建 / 更新角色时报 MalformedPolicyDocument。
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import tempfile

ISS = "token.actions.githubusercontent.com"
PROVIDER = f"arn:aws:iam::111122223333:oidc-provider/{ISS}"

TOKENS = {
    "T1 main 推送（旧格式）": {"aud": "sts.amazonaws.com", "sub": "repo:example-org/cloudops-lab:ref:refs/heads/main"},
    "T2 feature 分支": {"aud": "sts.amazonaws.com", "sub": "repo:example-org/cloudops-lab:ref:refs/heads/feature/x"},
    "T3 pull_request": {"aud": "sts.amazonaws.com", "sub": "repo:example-org/cloudops-lab:pull_request"},
    "T4 环境 production": {"aud": "sts.amazonaws.com", "sub": "repo:example-org/cloudops-lab:environment:production"},
    "T5 main（新格式，含数字 ID）": {"aud": "sts.amazonaws.com", "sub": "repo:example-org@1234/cloudops-lab@5678:ref:refs/heads/main"},
    "T6 同名仓库被他人重建（新格式）": {"aud": "sts.amazonaws.com", "sub": "repo:example-org@1234/cloudops-lab@9999:ref:refs/heads/main"},
    "T7 别的仓库": {"aud": "sts.amazonaws.com", "sub": "repo:attacker/cloudops-lab:ref:refs/heads/main"},
}


def trust(sub_op: str | None, sub_val: str | None) -> dict:
    cond = {"StringEquals": {f"{ISS}:aud": "sts.amazonaws.com"}}
    if sub_op:
        cond.setdefault(sub_op, {})[f"{ISS}:sub"] = sub_val
    return {"Version": "2012-10-17", "Statement": [{
        "Effect": "Allow", "Principal": {"Federated": PROVIDER},
        "Action": "sts:AssumeRoleWithWebIdentity", "Condition": cond}]}


POLICIES = {
    "P1 精确：旧格式 main": trust("StringEquals", "repo:example-org/cloudops-lab:ref:refs/heads/main"),
    "P2 精确：新格式 main": trust("StringEquals", "repo:example-org@1234/cloudops-lab@5678:ref:refs/heads/main"),
    "P3 环境 production": trust("StringEquals", "repo:example-org/cloudops-lab:environment:production"),
    "P4 仓库内任意引用": trust("StringLike", "repo:example-org/cloudops-lab:*"),
    "P5 通配 repo:*（危险）": trust("StringLike", "repo:*"),
    "P6 没有 sub 条件（会被 IAM 拒绝）": trust(None, None),
}


def provider_controls_ok(policy: dict) -> tuple[bool, str]:
    """模拟 IAM 的 identity-provider controls：必须评估 sub / job_workflow_ref，且不能只是通配符。"""
    for st in policy["Statement"]:
        for op, kv in st.get("Condition", {}).items():
            for k, v in kv.items():
                if k in (f"{ISS}:sub", f"{ISS}:job_workflow_ref"):
                    vals = v if isinstance(v, list) else [v]
                    if all(x.strip("*") in ("", "repo:") for x in vals):
                        return False, "sub 只有通配符"
                    return True, "ok"
    return False, "没有评估 sub 或 job_workflow_ref → MalformedPolicyDocument"


def assumable(policy: dict, claims: dict) -> bool:
    for st in policy["Statement"]:
        ok = True
        for op, kv in st.get("Condition", {}).items():
            for k, want in kv.items():
                have = claims.get(k.split(":")[-1])
                wants = want if isinstance(want, list) else [want]
                if op == "StringEquals" and have not in wants:
                    ok = False
                if op == "StringLike" and not any(fnmatch.fnmatchcase(have or "", w) for w in wants):
                    ok = False
        if ok and st["Effect"] == "Allow":
            return True
    return False


def analyzer(policy: dict) -> list[str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(policy, fh)
        path = fh.name
    try:
        r = subprocess.run(["aws", "accessanalyzer", "validate-policy", "--policy-type", "RESOURCE_POLICY",
                            "--validate-policy-resource-type", "AWS::IAM::AssumeRolePolicyDocument",
                            "--policy-document", f"file://{path}", "--output", "json"],
                           capture_output=True, text=True, env=dict(os.environ, MSYS_NO_PATHCONV="1"))
        if r.returncode:
            return [f"调用失败：{r.stderr.strip()[:60]}"]
        return [f"{f['findingType']}:{f['issueCode']}" for f in json.loads(r.stdout)["findings"]]
    finally:
        os.unlink(path)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aws", action="store_true")
    a = ap.parse_args()
    for pname, pol in POLICIES.items():
        ok, why = provider_controls_ok(pol)
        print(f"\n{pname}  ——  IAM 提供商控制：{'通过' if ok else '拒绝（' + why + '）'}")
        if a.aws:
            print("   Access Analyzer：" + (", ".join(analyzer(pol)) or "无发现"))
        if not ok:
            continue
        for tname, claims in TOKENS.items():
            print(f"   {'✓' if assumable(pol, claims) else '·'} {tname}")


if __name__ == "__main__":
    main()
