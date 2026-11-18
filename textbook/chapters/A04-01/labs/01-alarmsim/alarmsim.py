#!/usr/bin/env python3
"""alarmsim：CloudWatch 指标告警的评估模型（第 08 讲实验 8-1，离线、零费用）。

    python alarmsim.py table          # 复现 AWS 文档中两张“缺失数据”判定表（10 种序列 × 4 种处理 = 40 个结果）
    python alarmsim.py timeline       # 情境中的两条告警：基线 → 故障 → 恢复 → 停发数据，逐分钟的状态

实现依据：《Configuring how CloudWatch alarms treat missing data》（滑动窗口，默认）：
  1 取最近“评估范围”个数据点（本模型取 N+2，与文档示例一致）；
  2 最近 N 个点都存在 → 只看这 N 个；
  3 有缺失，但范围内真实点 ≥ N → 用最近 N 个真实点（此时不需要缺失数据处理）；
  4 真实点 < N → 按 treat_missing_data 补齐；missing / ignore 时只看真实点，
    并应用“过早告警”规则：真实点少于 M、且最近 N 期里最早的越界点已至少 M 期“老”、
    其后都是越界或缺失 → missing 判 ALARM，ignore 保持原状态。
"""
from __future__ import annotations

import argparse

OK, ALARM, INSUFFICIENT = "OK", "ALARM", "INSUFFICIENT_DATA"


def evaluate(points: list, m: int, n: int, treat: str = "missing", current: str = INSUFFICIENT,
             breach=lambda v: v == "X", eval_range: int | None = None) -> str:
    """points：从旧到新，None 表示缺失。返回新的告警状态。"""
    r = eval_range or n + 2
    win = points[-r:]
    last_n = win[-n:]
    real = [p for p in win if p is not None]

    if len(last_n) == n and all(p is not None for p in last_n):
        return ALARM if sum(breach(p) for p in last_n) >= m else OK
    if len(real) >= n:
        return ALARM if sum(breach(p) for p in real[-n:]) >= m else OK
    if not real:
        return {"missing": INSUFFICIENT, "ignore": current, "breaching": ALARM, "notBreaching": OK}[treat]

    breaching_real = sum(breach(p) for p in real)
    fills = n - len(real)
    if treat == "breaching":
        return ALARM if breaching_real + fills >= m else OK
    if treat == "notBreaching":
        return ALARM if breaching_real >= m else OK

    # missing / ignore：先看“过早告警”规则
    ages = [len(last_n) - i for i, p in enumerate(last_n)]                # 最新的点年龄为 1
    breach_ages = [a for a, p in zip(ages, last_n) if p is not None and breach(p)]
    if len(real) < m and breach_ages:
        oldest = max(breach_ages)
        newer_ok = all(p is None or breach(p) for a, p in zip(ages, last_n) if a < oldest)
        if oldest >= m and newer_ok:
            return ALARM if treat == "missing" else current
    return ALARM if breaching_real >= m else OK


def parse(seq: str) -> list:
    return [None if c == "-" else c for c in seq.split()]


# AWS 文档中的两张表：(序列, M, N, {处理方式: 结果})；“retain”表示保持当前状态
OFFICIAL = [
    ("0 - X - X", 3, 3, {"missing": OK, "ignore": OK, "breaching": OK, "notBreaching": OK}),
    ("0 - - - -", 3, 3, {"missing": OK, "ignore": OK, "breaching": OK, "notBreaching": OK}),
    ("- - - - -", 3, 3, {"missing": INSUFFICIENT, "ignore": "retain", "breaching": ALARM, "notBreaching": OK}),
    ("0 X X - X", 3, 3, {"missing": ALARM, "ignore": ALARM, "breaching": ALARM, "notBreaching": ALARM}),
    ("- - X - -", 3, 3, {"missing": ALARM, "ignore": "retain", "breaching": ALARM, "notBreaching": OK}),
    ("0 - X - X", 2, 3, {"missing": ALARM, "ignore": ALARM, "breaching": ALARM, "notBreaching": ALARM}),
    ("0 0 X 0 X", 2, 3, {"missing": ALARM, "ignore": ALARM, "breaching": ALARM, "notBreaching": ALARM}),
    ("0 - X - -", 2, 3, {"missing": OK, "ignore": OK, "breaching": ALARM, "notBreaching": OK}),
    ("- - - - 0", 2, 3, {"missing": OK, "ignore": OK, "breaching": ALARM, "notBreaching": OK}),
    ("- - - X -", 2, 3, {"missing": ALARM, "ignore": "retain", "breaching": ALARM, "notBreaching": OK}),
]


def table() -> int:
    ok = 0
    print(f"{'序列':<12}{'M/N':<6}{'missing':<20}{'ignore':<20}{'breaching':<12}{'notBreaching':<12}")
    for seq, m, n, want in OFFICIAL:
        cells = []
        for t in ("missing", "ignore", "breaching", "notBreaching"):
            got = evaluate(parse(seq), m, n, t, current="(原状态)")
            exp = "(原状态)" if want[t] == "retain" else want[t]
            ok += got == exp
            cells.append(f"{got}{'' if got == exp else '≠' + exp}")
        print(f"{seq:<12}{f'{m}/{n}':<6}{cells[0]:<20}{cells[1]:<20}{cells[2]:<12}{cells[3]:<12}")
    print(f"\n与 AWS 文档一致：{ok} / {len(OFFICIAL) * 4}")
    return ok


def timeline() -> None:
    # 每分钟一个数据点；None 表示这一分钟没有上报
    phases = [("基线", 3, 0, 1), ("故障", 2, 2, 1), ("恢复", 3, 0, 1), ("停发", 5, None, None)]
    err_state, hb_state = INSUFFICIENT, INSUFFICIENT
    errs, hbs, minute = [], [], 0
    print(f"{'分钟':<6}{'阶段':<6}{'Errors(Sum)':<13}{'Heartbeat(Min)':<16}{'错误告警 2/3 notBreaching':<28}{'心跳告警 3/3 breaching'}")
    for name, k, e, h in phases:
        for _ in range(k):
            minute += 1
            errs.append(e)
            hbs.append(h)
            err_state = evaluate(errs, 2, 3, "notBreaching", err_state, breach=lambda v: v >= 1)
            hb_state = evaluate(hbs, 3, 3, "breaching", hb_state, breach=lambda v: v < 1)
            show = lambda v: "—" if v is None else str(v)
            print(f"T{minute:<5}{name:<6}{show(e):<13}{show(h):<16}{err_state:<28}{hb_state}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["table", "timeline"])
    a = ap.parse_args()
    table() if a.cmd == "table" else timeline()


if __name__ == "__main__":
    main()
