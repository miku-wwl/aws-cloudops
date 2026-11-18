#!/usr/bin/env python3
"""ctquery：只读查询 CloudTrail 事件历史，并在输出前脱敏（第 11 讲实验 11-2）。

    python ctquery.py --name PutBucketTagging --hours 24
    python ctquery.py --resource a11-lab01-xxxx --hours 2         # 按资源名（如桶名）查
    python ctquery.py --name TestEventPattern --max 1 --raw       # 打印脱敏后的完整事件 JSON

事件历史的边界（官方）：只有管理事件（不含数据事件、Insights、网络活动事件）；最近 90 天；
单账户、单区域；每次只能用一个属性过滤（外加时间范围）；查看不收费。
本工具调用 aws cloudtrail lookup-events（只读），不需要 boto3。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ACCOUNT = re.compile(r"(?<!\d)\d{12}(?!\d)")
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
ACCESS_KEY = re.compile(r"\b(AKIA|ASIA)[A-Z0-9]{12,}\b")


def redact(obj, names: dict | None = None):
    """递归脱敏：12 位账户号 → 111122223333；IPv4 → 203.0.113.x；访问密钥 → AKIA****；
    names 里给出的身份名（用户名、会话名）替换为占位符。"""
    if isinstance(obj, dict):
        return {k: redact(v, names) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v, names) for v in obj]
    if not isinstance(obj, str):
        return obj
    s = ACCOUNT.sub("111122223333", obj)
    s = IPV4.sub("203.0.113.x", s)
    s = ACCESS_KEY.sub(lambda m: m.group(1) + "****", s)
    for real, alias in (names or {}).items():
        s = s.replace(real, alias)
    return s


def identity_names(event: dict) -> dict:
    """从 userIdentity 里取出真实的用户名 / 会话名，映射成稳定的占位符。"""
    ui = event.get("userIdentity", {})
    out = {}
    if ui.get("userName"):
        out[ui["userName"]] = "<user>"
    arn = ui.get("arn", "")
    if ":assumed-role/" in arn:
        role, _, session = arn.split(":assumed-role/")[1].partition("/")
        if session:
            out[session] = "<session>"
    return out


def summarize(event: dict) -> dict:
    ui = event.get("userIdentity", {})
    rp = event.get("requestParameters")
    if isinstance(rp, dict) and rp.get("isRedacted"):
        params = f"（CloudTrail 已隐藏：{rp.get('reason')}）"
    elif isinstance(rp, dict):
        params = ", ".join(sorted(rp))
    else:
        params = "null"
    return {"eventTime": event.get("eventTime"), "eventName": event.get("eventName"),
            "eventSource": event.get("eventSource"), "readOnly": event.get("readOnly"),
            "errorCode": event.get("errorCode") or "-", "identity": ui.get("type"),
            "requestParameters": params, "eventID": event.get("eventID", "")[:8] + "…"}


def lookup(attr_key: str, attr_value: str, hours: int, region: str, max_items: int) -> list[dict]:
    start = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    cmd = ["aws", "cloudtrail", "lookup-events", "--region", region, "--output", "json",
           "--lookup-attributes", f"AttributeKey={attr_key},AttributeValue={attr_value}",
           "--start-time", start, "--max-items", str(max_items), "--query", "Events[].CloudTrailEvent"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        sys.exit(p.stderr.strip())
    return [json.loads(e) for e in json.loads(p.stdout or "[]") or []]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--name", help="EventName，例如 PutBucketTagging")
    g.add_argument("--resource", help="ResourceName，例如桶名")
    g.add_argument("--source", help="EventSource，例如 s3.amazonaws.com")
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--max", type=int, default=10)
    ap.add_argument("--raw", action="store_true", help="打印脱敏后的完整事件")
    a = ap.parse_args()
    key, value = (("EventName", a.name) if a.name else ("ResourceName", a.resource) if a.resource
                  else ("EventSource", a.source))
    events = lookup(key, value, a.hours, a.region, a.max)
    print(f"{key}={value}，最近 {a.hours} 小时，{a.region}：{len(events)} 条")
    for ev in events:
        names = identity_names(ev)
        if a.raw:
            print(json.dumps(redact(ev, names), ensure_ascii=False, indent=1))
            continue
        for k, v in redact(summarize(ev), names).items():
            print(f"  {k:18} {v}")
        print()


if __name__ == "__main__":
    main()
