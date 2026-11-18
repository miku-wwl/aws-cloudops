#!/usr/bin/env python3
"""patterns：EventBridge 事件模式匹配器（第 09 讲实验 9-2）。

    python patterns.py                 # 离线：本地匹配器 vs 已录制的 AWS 实测结果（aws_results.json）
    python patterns.py --live          # 在线：逐条调用 aws events test-event-pattern 并重新录制
    python patterns.py --explain C14   # 打印某个用例的模式与事件

TestEventPattern 只做计算、不创建任何资源，也不产生 EventBridge 事件费用。
本地匹配器实现的规则（均以官方文档为准，并用 --live 实测核对）：
  1. 模式里的多个字段之间是 AND；同一字段数组里的多个值之间是 OR；
  2. 事件值是数组时，与模式数组有交集即命中；
  3. 精确匹配区分大小写、区分类型（"500" 与 500 不同）；
  4. 缺失字段只能被 {"exists": false} 命中；null 只匹配显式的 null；
  5. 比较运算符只作用于叶子节点（exists 用在对象上不会命中）；
  6. prefix / suffix / equals-ignore-case / wildcard / anything-but / numeric / cidr / $or。
"""
from __future__ import annotations

import argparse
import copy
import ipaddress
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
MISSING = object()
NUM = (int, float)


def _is_num(v) -> bool:
    return isinstance(v, NUM) and not isinstance(v, bool)


def _wildcard(pattern: str) -> re.Pattern:
    out, i = "", 0
    while i < len(pattern):
        c = pattern[i]
        if c == "\\" and i + 1 < len(pattern):           # \* 与 \\ 表示字面量
            out += re.escape(pattern[i + 1])
            i += 2
            continue
        out += ".*" if c == "*" else re.escape(c)
        i += 1
    return re.compile(out + r"\Z", re.S)


def _str_op(arg, v, op) -> bool:
    if not isinstance(v, str):
        return False
    if isinstance(arg, dict):                             # {"prefix": {"equals-ignore-case": "x"}}
        arg, v = arg["equals-ignore-case"].lower(), v.lower()
    return getattr(v, op)(arg)


def _numeric(cond: list, v) -> bool:
    if not _is_num(v):
        return False
    ops = {"=": v.__eq__, "<": v.__lt__, "<=": v.__le__, ">": v.__gt__, ">=": v.__ge__}
    return all(ops[cond[i]](cond[i + 1]) for i in range(0, len(cond), 2))


def _one(m, v) -> bool:
    """一个叶子匹配器 m 对一个事件值 v。"""
    if m is None:
        return v is None
    if isinstance(m, bool) or isinstance(v, bool):
        return m is v
    if isinstance(m, str):
        return isinstance(v, str) and v == m
    if _is_num(m):
        return _is_num(v) and float(v) == float(m)
    if not isinstance(m, dict) or len(m) != 1:
        raise ValueError(f"无法识别的匹配器：{m!r}")
    (op, arg), = m.items()
    if op == "prefix":
        return _str_op(arg, v, "startswith")
    if op == "suffix":
        return _str_op(arg, v, "endswith")
    if op == "equals-ignore-case":
        return isinstance(v, str) and v.lower() == arg.lower()
    if op == "wildcard":
        return isinstance(v, str) and _wildcard(arg).match(v) is not None
    if op == "numeric":
        return _numeric(arg, v)
    if op == "cidr":
        try:
            return isinstance(v, str) and ipaddress.ip_address(v) in ipaddress.ip_network(arg, strict=False)
        except ValueError:
            return False
    if op == "exists":
        return bool(arg)                                  # 走到这里说明字段存在
    if op == "anything-but":
        if isinstance(arg, dict):                         # anything-but 的 prefix/suffix/wildcard/ignore-case 形式
            (inner, vals), = arg.items()
            vals = vals if isinstance(vals, list) else [vals]
            return not any(_one({inner: x}, v) for x in vals)
        vals = arg if isinstance(arg, list) else [arg]
        return not any(_one(x, v) for x in vals)
    raise ValueError(f"本地匹配器未实现运算符：{op}")


def _leaf(matchers: list, ev) -> bool:
    if ev is MISSING:
        return any(isinstance(m, dict) and m.get("exists") is False for m in matchers)
    if isinstance(ev, dict):
        return False                                      # 运算符只作用于叶子
    values = ev if isinstance(ev, list) else [ev]
    for m in matchers:
        if isinstance(m, dict) and m.get("exists") is False:
            continue                                      # 字段存在 → exists:false 不命中
        if any(_one(m, v) for v in values):
            return True
    return False


def match(pattern: dict, event) -> bool:
    for key, pv in pattern.items():
        if key == "$or":
            if not any(match(sub, event) for sub in pv):
                return False
            continue
        ev = event.get(key, MISSING) if isinstance(event, dict) else MISSING
        if isinstance(pv, dict):
            if not match(pv, ev if isinstance(ev, dict) else {}):
                return False
        elif isinstance(pv, list):
            if not _leaf(pv, ev):
                return False
        else:
            raise ValueError(f"模式里 {key} 的值必须是数组或对象")
    return True


# --------------------------------------------------------------------------- 用例与实测
def load_cases():
    spec = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    for c in spec["cases"]:
        event = copy.deepcopy(spec["base"])
        event.update(c["envelope"])
        event["detail"].update(c["detail"])
        pattern = spec["lab_pattern"] if c["pattern"] == "lab" else c["pattern"]
        yield c["id"], c["title"], pattern, event


def aws_test(pattern: dict, event: dict, region: str):
    cmd = ["aws", "events", "test-event-pattern", "--region", region, "--output", "json",
           "--event-pattern", json.dumps(pattern, ensure_ascii=False), "--event", json.dumps(event, ensure_ascii=False)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        err = p.stderr.strip().splitlines()[-1] if p.stderr.strip() else "error"
        return "error: " + re.sub(r"\s+", " ", err)[:160]
    return json.loads(p.stdout)["Result"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--explain")
    a = ap.parse_args()
    store = HERE / "aws_results.json"
    recorded = json.loads(store.read_text(encoding="utf-8")) if store.exists() else {"results": {}}
    rows, mismatches, fresh = [], 0, {}
    for cid, title, pattern, event in load_cases():
        if a.explain and a.explain != cid:
            continue
        if a.explain:
            print("pattern =", json.dumps(pattern, ensure_ascii=False))
            print("detail  =", json.dumps(event["detail"], ensure_ascii=False), "| source =", event["source"])
        local = match(pattern, event)
        remote = aws_test(pattern, event, a.region) if a.live else recorded["results"].get(cid)
        fresh[cid] = remote
        agree = remote == local
        mismatches += 0 if agree else 1
        rows.append((cid, title, local, remote, "✓" if agree else "✗"))
    for cid, title, local, remote, ok in rows:
        print(f"{cid}  {str(local):5}  AWS={str(remote):5}  {ok}  {title}")
    print(f"\n{len(rows)} 个用例，本地与 AWS 不一致：{mismatches}")
    if a.live and not a.explain:
        store.write_text(json.dumps({"recorded": str(date.today()), "api": "events:TestEventPattern",
                                     "region": a.region, "results": fresh}, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
        print(f"已录制到 {store.name}")
    sys.exit(1 if mismatches else 0)


if __name__ == "__main__":
    main()
