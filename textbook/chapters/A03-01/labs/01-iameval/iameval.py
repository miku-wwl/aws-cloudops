#!/usr/bin/env python3
"""iameval：教学用 IAM 策略评估器（第 06 讲实验 6-1）。

    python iameval.py scenarios.json            # 本地引擎逐个场景给出判定与理由
    python iameval.py scenarios.json --aws      # 同时调用 AWS 官方模拟器 simulate-custom-policy 对照

按 AWS 文档《Policy evaluation logic》对单账户请求的顺序实现：
  1 显式拒绝：任何适用策略中的 Deny → explicitDeny
  2 SCP / RCP：存在但没有 Allow → implicitDeny
  3 资源策略：直接授予 IAM 用户 / 角色会话 ARN 的 Allow 可单独放行（同账户）
  4 身份策略：没有 Allow → implicitDeny
  5 权限边界：存在但不允许 → implicitDeny
  6 会话策略：存在但不允许 → implicitDeny
支持 Action / Resource / NotAction 通配符和 StringEquals / StringLike / Bool / ArnLike 条件。
这是“讲清机制”的模型，不覆盖所有服务的特殊规则。
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import shutil
import subprocess
import sys


def as_list(x):
    return x if isinstance(x, list) else [x]


def match(pattern: str, value: str, case_insensitive: bool = False) -> bool:
    if case_insensitive:
        pattern, value = pattern.lower(), value.lower()
    return fnmatch.fnmatchcase(value, pattern)


def cond_ok(cond: dict | None, ctx: dict) -> bool:
    if not cond:
        return True
    for op, kv in cond.items():
        for key, want in kv.items():
            have = ctx.get(key)
            if have is None:
                return False
            wants = [str(w) for w in as_list(want)]
            if op == "StringEquals" and str(have) not in wants:
                return False
            if op in ("StringLike", "ArnLike") and not any(match(w, str(have)) for w in wants):
                return False
            if op == "Bool" and str(have).lower() not in [w.lower() for w in wants]:
                return False
    return True


def principal_ok(stmt: dict, caller: str | None) -> bool:
    if "Principal" not in stmt:
        return True                                   # 身份策略、边界、会话策略、SCP 没有 Principal
    p = stmt["Principal"]
    if p == "*":
        return True
    arns = as_list(p.get("AWS", [])) if isinstance(p, dict) else []
    return caller is not None and any(a == "*" or match(a, caller) for a in arns)


def stmt_applies(stmt, action, resource, ctx, caller) -> bool:
    if "Action" in stmt and not any(match(a, action, True) for a in as_list(stmt["Action"])):
        return False
    if "NotAction" in stmt and any(match(a, action, True) for a in as_list(stmt["NotAction"])):
        return False
    if "Resource" in stmt and not any(match(r, resource) for r in as_list(stmt["Resource"])):
        return False
    return principal_ok(stmt, caller) and cond_ok(stmt.get("Condition"), ctx)


def find(policies, effect, action, resource, ctx, caller=None):
    """返回第一条匹配的语句标识（策略名#Sid），没有则 None。"""
    for name, pol in policies:
        for i, s in enumerate(as_list(pol.get("Statement", []))):
            if s.get("Effect") == effect and stmt_applies(s, action, resource, ctx, caller):
                return f"{name}#{s.get('Sid', i + 1)}"
    return None


def evaluate(sc: dict, action: str, resource: str) -> tuple[str, str]:
    ctx = sc.get("context", {})
    caller = sc.get("caller_arn")
    ident = [(f"identity{i + 1}", p) for i, p in enumerate(sc.get("identity", []))]
    rp = [("resource", sc["resource_policy"])] if sc.get("resource_policy") else []
    pb = [("boundary", sc["boundary"])] if sc.get("boundary") else []
    sp = [("session", sc["session_policy"])] if sc.get("session_policy") else []
    scp = [(f"scp{i + 1}", p) for i, p in enumerate(sc.get("scps", []))]

    hit = find(ident + rp + pb + sp + scp, "Deny", action, resource, ctx, caller)
    if hit:
        return "explicitDeny", f"显式拒绝：{hit}"
    if scp and not find(scp, "Allow", action, resource, ctx):
        return "implicitDeny", "SCP 中没有允许该操作的语句"
    res_allow = find(rp, "Allow", action, resource, ctx, caller)
    if res_allow and sc.get("principal_type") in ("user", "role-session"):
        return "allowed", f"资源策略直接授予调用者：{res_allow}（同账户，不受身份策略/边界的隐式拒绝限制）"
    id_allow = find(ident, "Allow", action, resource, ctx)
    if not id_allow and not res_allow:
        return "implicitDeny", "身份策略与资源策略都没有匹配的 Allow"
    if pb and not find(pb, "Allow", action, resource, ctx):
        return "implicitDeny", "权限边界不允许（边界只设上限，不授予权限）"
    if sp and not find(sp, "Allow", action, resource, ctx):
        return "implicitDeny", "会话策略不允许（只能收窄角色权限）"
    return "allowed", f"允许：{id_allow or res_allow}"


# ------------------------------------------------------------------ AWS 官方模拟器对照
def aws_simulate(sc: dict) -> dict[str, str]:
    cmd = ["aws", "iam", "simulate-custom-policy", "--output", "json",
           "--action-names", sc["action"], "--resource-arns", *sc["resources"],
           "--policy-input-list", *[json.dumps(p) for p in sc.get("identity", [{"Version": "2012-10-17", "Statement": []}])]]
    if sc.get("boundary"):
        cmd += ["--permissions-boundary-policy-input-list", json.dumps(sc["boundary"])]
    if sc.get("resource_policy"):
        cmd += ["--resource-policy", json.dumps(sc["resource_policy"]), "--caller-arn", sc["caller_arn"],
                "--resource-owner", sc["resource_owner"]]
    for k, v in sc.get("context", {}).items():
        typ = "boolean" if str(v).lower() in ("true", "false") else "string"
        cmd += ["--context-entries", f"ContextKeyName={k},ContextKeyValues={v},ContextKeyType={typ}"]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if out.returncode:
        return {r: f"ERROR: {out.stderr.strip()[:80]}" for r in sc["resources"]}
    res = json.loads(out.stdout)["EvaluationResults"][0]
    per = {x["EvalResourceName"]: x["EvalResourceDecision"] for x in res.get("ResourceSpecificResults", [])}
    return per or {sc["resources"][0]: res["EvalDecision"]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenarios")
    ap.add_argument("--aws", action="store_true", help="同时调用 AWS IAM simulate-custom-policy（只读、免费）")
    a = ap.parse_args()
    with open(a.scenarios, encoding="utf-8") as fh:
        scenarios = json.load(fh)
    if a.aws and not shutil.which("aws"):
        sys.exit("需要 AWS CLI")
    mismatches = 0
    for sc in scenarios:
        if sc.get("local_only") and a.aws:
            print(f"\n[{sc['name']}] {sc['title']}（只在本地评估：模拟器不支持该策略类型）")
        else:
            print(f"\n[{sc['name']}] {sc['title']}")
        aws = aws_simulate(sc) if a.aws and not sc.get("local_only") else {}
        for r in sc["resources"]:
            dec, why = evaluate(sc, sc["action"], r)
            exp = sc.get("expect", {}).get(r)
            mark = "" if exp is None else ("  ✓预期" if dec == exp else f"  ✗预期 {exp}")
            line = f"  {r.split(':::')[-1]:<34} 本地={dec:<13}"
            if aws:
                same = aws.get(r) == dec
                mismatches += not same
                line += f" AWS={aws.get(r):<13} {'一致' if same else '不一致'}"
            print(line + mark)
            print(f"      ↳ {why}")
    if a.aws:
        print(f"\n与 AWS 模拟器不一致的判定：{mismatches} 处")
        sys.exit(1 if mismatches else 0)


if __name__ == "__main__":
    main()
