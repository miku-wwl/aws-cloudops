#!/usr/bin/env python3
"""twogates：SSE-KMS 对象读写要过的“两道门”（第 12 讲实验 12-1，离线、零费用）。

    python twogates.py scenarios.json

第一道门 S3：身份策略允许该 S3 动作，且桶策略没有显式拒绝（例如非 TLS 请求）；
             对公开主体还要看 Block Public Access（BPA）。
第二道门 KMS：S3 代表调用者向 KMS 请求 GenerateDataKey（写）或 Decrypt（读）——
             密钥策略必须直接授权该主体，或把权限委托给本账户的 IAM（"root" 语句），
             此时调用者自己的身份策略还要允许对应的 kms 动作（常配 kms:ViaService 条件）。
             S3 Bucket Key 只是减少 KMS 调用次数，不改变授权要求。
任何一道门不过，S3 返回的都是 403 AccessDenied——要看错误信息里提到的是 S3 还是 KMS。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

KMS_FOR = {"PutObject": ["kms:GenerateDataKey"], "GetObject": ["kms:Decrypt"],
           "MultipartUpload": ["kms:GenerateDataKey", "kms:Decrypt"]}   # 分段上传合并时需要解密数据密钥
S3_FOR = {"PutObject": "s3:PutObject", "GetObject": "s3:GetObject", "MultipartUpload": "s3:PutObject"}


def s3_gate(sc: dict) -> tuple[bool, str]:
    req, who, bucket = sc["request"], sc["principal"], sc["bucket"]
    if who.get("public"):
        if bucket.get("bpa", True):
            return False, "BPA：拒绝公开访问（RestrictPublicBuckets / BlockPublicPolicy）"
    if not req.get("tls", True) and bucket.get("deny_insecure_transport", True):
        return False, "桶策略显式拒绝：aws:SecureTransport = false"
    if req.get("acl") and bucket.get("owner_enforced", True):
        return False, "BucketOwnerEnforced：请求带 ACL 被拒（AccessControlListNotSupported）"
    action = S3_FOR[req["op"]]
    if action not in who.get("s3_actions", []):
        return False, f"身份策略没有允许 {action}"
    return True, f"允许 {action}"


def kms_gate(sc: dict) -> tuple[bool, str]:
    req, who, key = sc["request"], sc["principal"], sc["key"]
    if req.get("sse") != "aws:kms":
        return True, "对象不是 SSE-KMS：不经过 KMS"
    if key.get("state", "Enabled") != "Enabled":
        return False, f"密钥状态是 {key['state']}：任何调用都会失败"
    needed = KMS_FOR[req["op"]]
    direct = set(key.get("direct_grants", {}).get(who["name"], []))
    if all(a in direct or "kms:*" in direct for a in needed):
        return True, "密钥策略直接授权该主体"
    if not key.get("root_delegation", True):
        return False, "密钥策略既没点名该主体，也没有委托给本账户 IAM"
    have = set(who.get("kms_actions", []))
    missing = [a for a in needed if a not in have]
    if missing:
        return False, f"密钥策略委托给 IAM，但身份策略缺少 {', '.join(missing)}"
    if who.get("kms_via_s3_only") and not req.get("via_s3", True):
        return False, "身份策略要求 kms:ViaService = s3，直接调用 KMS 被拒"
    return True, "密钥策略委托 + 身份策略允许"


def evaluate(sc: dict) -> dict:
    ok1, why1 = s3_gate(sc)
    if not ok1:
        return {"result": "AccessDenied（S3 门）", "s3": why1, "kms": "未到达"}
    ok2, why2 = kms_gate(sc)
    return {"result": "成功" if ok2 else "AccessDenied（KMS 门）", "s3": why1, "kms": why2}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenarios")
    a = ap.parse_args()
    for sc in json.loads(Path(a.scenarios).read_text(encoding="utf-8"))["scenarios"]:
        r = evaluate(sc)
        print(f"{sc['id']:4} {sc['title']}")
        print(f"     S3 门：{r['s3']}\n     KMS 门：{r['kms']}\n     → {r['result']}")


if __name__ == "__main__":
    main()
