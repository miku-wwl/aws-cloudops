"""ticket-query：失败率可控的查询函数（第 02 讲实验）。

FAIL_RATE 是 0~1 之间的小数：0 表示从不失败，0.2 表示约 20% 的调用抛出异常。
未捕获的异常会让同步调用返回 StatusCode=200，但响应带有 FunctionError=Unhandled。
"""
import os
import random


def handler(event, context):
    fail_rate = float(os.environ.get("FAIL_RATE", "0"))
    if random.random() < fail_rate:
        raise RuntimeError(f"injected failure (FAIL_RATE={fail_rate})")
    ticket_id = (event or {}).get("ticket_id", "T-0000")
    return {"ticket_id": ticket_id, "status": "open", "request_id": context.aws_request_id}
