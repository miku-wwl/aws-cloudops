#!/usr/bin/env python3
"""s3tagged：S3 标签的两种写法 + S3_BUCKET_TAGGED 规则（第 11 讲实验 11-1，离线、零费用）。

    python s3tagged.py            # 回放“Owner 标签不见了”的事故时间线
    python s3tagged.py --abac     # 同样的操作改走 TagResource（S3 ABAC 的标签 API）

要点（与官方文档一致）：
  * PutBucketTagging 用请求里的标签集“整体替换”现有标签——只想加一个标签，却会把没写进去的全部删掉。
  * TagResource 只增加 / 覆盖请求里的键；UntagResource 只删除指定的键（可以用 aws:TagKeys 做权限条件）。
    对开启了 ABAC 的通用存储桶，PutBucketTagging 会被拒绝，只能用 TagResource（2025-11 起）。
  * 托管规则 S3_BUCKET_TAGGED：没有任何标签 → NON_COMPLIANT；给了 requiredKeyTags（逗号分隔、
    区分大小写）而缺任何一个键 → NON_COMPLIANT；不检查以 aws: 开头的标签。
"""
from __future__ import annotations

import argparse
import unicodedata


def put_bucket_tagging(tags: dict, tag_set: dict) -> dict:
    """整体替换：返回的就是请求里的标签集。"""
    return dict(tag_set)


def tag_resource(tags: dict, new: dict) -> dict:
    out = dict(tags)
    out.update(new)
    return out


def untag_resource(tags: dict, keys: list[str]) -> dict:
    return {k: v for k, v in tags.items() if k not in keys}


def s3_bucket_tagged(tags: dict, required_key_tags: str | None = None) -> str:
    user_tags = {k: v for k, v in tags.items() if not k.startswith("aws:")}
    if not user_tags:
        return "NON_COMPLIANT"
    if required_key_tags:
        required = [k.strip() for k in required_key_tags.split(",") if k.strip()]
        if any(k not in user_tags for k in required):
            return "NON_COMPLIANT"
    return "COMPLIANT"


BASELINE = {"Project": "aws-cloudops", "Environment": "sandbox", "Owner": "cloudops-lab", "Chapter": "A06-01"}


def timeline(abac: bool) -> list[tuple[str, str, dict]]:
    """回放事故：同一个意图（“给桶加 CostCenter 标签”），两种 API，两种结果。"""
    rows = [("09:00", "Terraform 创建的基线", dict(BASELINE))]
    if not abac:
        tags = put_bucket_tagging(BASELINE, {"Project": "aws-cloudops", "CostCenter": "cc-42"})
        rows.append(("09:03", "PutBucketTagging 只写了两个标签", tags))
        rows.append(("09:10", "terraform apply 回到代码里的标签集", dict(BASELINE)))   # CostCenter 也被删：它不在代码里
    else:
        tags = tag_resource(BASELINE, {"CostCenter": "cc-42"})
        rows.append(("09:03", "TagResource 只加 CostCenter", tags))
        rows.append(("09:05", "UntagResource Owner（被拒，见实验 11-3）", tags))
    return rows


def pad(s: str, width: int) -> str:
    """按显示宽度补空格（中文占两格），让终端输出对齐。"""
    w = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)
    return s + " " * max(0, width - w)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--abac", action="store_true")
    a = ap.parse_args()
    print(pad("时间", 7) + pad("操作", 42) + pad("Owner", 14) + "S3_BUCKET_TAGGED")
    for t, what, tags in timeline(a.abac):
        print(pad(t, 7) + pad(what, 42) + pad(tags.get("Owner", "（无）"), 14) + s3_bucket_tagged(tags, "Owner"))
        print(" " * 7 + "标签：" + ", ".join(sorted(tags)))


if __name__ == "__main__":
    main()
