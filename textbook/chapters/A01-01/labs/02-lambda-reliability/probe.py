#!/usr/bin/env python3
"""从“调用方”视角探测 ticket-query，并计算请求型 SLI（第 02 讲实验 2-3）。

    # 离线演示（不需要 AWS）：
    python probe.py --simulate --count 1000 --error-rate 0.002 --throttle-rate 0.003 --seed 7
    # 真实探测（需要凭证；会产生极少量 Lambda 调用费用）：
    python probe.py --function-name ticket-query --count 200 --region us-east-1

真实模式关闭了 SDK 的自动重试（max_attempts=1）：默认的“standard”重试模式会把
被限流的请求悄悄重试成功，调用方看到的成功率会比函数真实承受的压力好看。
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter

OK, FUNC_ERR, THROTTLED, OTHER = "ok", "function_error", "throttled", "other_error"


def invoke_real(fn: str, region: str, count: int) -> Counter:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError

    client = boto3.client("lambda", region_name=region, config=Config(retries={"max_attempts": 1, "mode": "standard"}))
    c = Counter()
    for i in range(count):
        try:
            resp = client.invoke(FunctionName=fn, Payload=json.dumps({"ticket_id": f"T-{i:04d}"}).encode())
            c[FUNC_ERR if "FunctionError" in resp else OK] += 1
        except ClientError as e:
            c[THROTTLED if e.response["Error"]["Code"] == "TooManyRequestsException" else OTHER] += 1
    return c


def invoke_simulated(count: int, error_rate: float, throttle_rate: float, seed: int) -> Counter:
    rnd, c = random.Random(seed), Counter()
    for _ in range(count):
        x = rnd.random()
        c[THROTTLED if x < throttle_rate else FUNC_ERR if x < throttle_rate + error_rate else OK] += 1
    return c


def report(c: Counter, slo: float) -> None:
    total = sum(c.values())
    executed = c[OK] + c[FUNC_ERR]            # 只有真正执行过的调用才计入 Invocations
    print(f"请求总数 {total}：成功 {c[OK]}，函数错误 {c[FUNC_ERR]}，限流 {c[THROTTLED]}，其他 {c[OTHER]}")
    if executed:
        print(f"函数层 (Invocations-Errors)/Invocations = {c[OK]}/{executed} = {c[OK] / executed:.3%}")
    sli = c[OK] / total if total else float("nan")
    print(f"调用方 SLI = 成功 / 全部请求 = {c[OK]}/{total} = {sli:.3%}  （SLO {slo:.1%}：{'达标' if sli >= slo else '未达标'}）")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--function-name", default="ticket-query")
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--count", type=int, default=100)
    ap.add_argument("--slo", type=float, default=0.999)
    ap.add_argument("--simulate", action="store_true")
    ap.add_argument("--error-rate", type=float, default=0.0)
    ap.add_argument("--throttle-rate", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    c = invoke_simulated(a.count, a.error_rate, a.throttle_rate, a.seed) if a.simulate else invoke_real(a.function_name, a.region, a.count)
    report(c, a.slo)


if __name__ == "__main__":
    main()
