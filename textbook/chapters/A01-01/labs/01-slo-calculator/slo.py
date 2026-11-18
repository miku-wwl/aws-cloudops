#!/usr/bin/env python3
"""SLO / 错误预算 / 燃烧率计算器（第 02 讲实验 2-1，纯本地，无需 AWS）。

    python slo.py request --total 1003 --bad 5 --slo 99.9
    python slo.py period  --days 30 --slo 99.9
    python slo.py burn    --slo 99.9 --interval-days 30 --budget-pct 2 --window-hours 1
    python slo.py table   --slo 99.9 --interval-days 30

公式（与 CloudWatch Application Signals 文档一致）：
    SLI(请求型)        = 好请求 / 总请求
    错误预算(请求型)   = 总请求 × (1 − SLO)
    错误预算(时间型)   = 区间分钟数 × (1 − SLO)
    燃烧率             = 回看窗口内的错误率 / (1 − SLO)
    燃烧率告警阈值     = 允许在窗口内消耗的预算比例 × 区间长度 / 窗口长度
    错误率阈值         = 燃烧率阈值 × (1 − SLO)
"""
from __future__ import annotations

import argparse


def pct(x: float) -> float:
    """99.9 → 0.999；0.999 → 0.999"""
    return x / 100 if x > 1 else x


def request_sli(total: int, bad: int) -> float:
    if total <= 0:
        raise ValueError("total 必须大于 0：没有请求就没有 SLI（0/0 无意义）")
    return (total - bad) / total


def request_budget(total: int, slo: float) -> float:
    return total * (1 - slo)


def period_budget_minutes(days: float, slo: float) -> float:
    return days * 24 * 60 * (1 - slo)


def burn_rate(error_rate: float, slo: float) -> float:
    return error_rate / (1 - slo)


def burn_threshold(budget_fraction: float, interval_hours: float, window_hours: float) -> float:
    return budget_fraction * interval_hours / window_hours


def error_ratio_threshold(burn: float, slo: float) -> float:
    return burn * (1 - slo)


def hours_to_exhaustion(burn: float, interval_hours: float, remaining: float = 1.0) -> float:
    return remaining * interval_hours / burn


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("request"); r.add_argument("--total", type=int, required=True)
    r.add_argument("--bad", type=int, required=True); r.add_argument("--slo", type=float, required=True)
    p = sub.add_parser("period"); p.add_argument("--days", type=float, required=True)
    p.add_argument("--slo", type=float, required=True)
    b = sub.add_parser("burn"); b.add_argument("--slo", type=float, required=True)
    b.add_argument("--interval-days", type=float, default=30); b.add_argument("--budget-pct", type=float, required=True)
    b.add_argument("--window-hours", type=float, required=True)
    t = sub.add_parser("table"); t.add_argument("--slo", type=float, required=True)
    t.add_argument("--interval-days", type=float, default=30)
    a = ap.parse_args()

    if a.cmd == "request":
        slo = pct(a.slo)
        sli = request_sli(a.total, a.bad)
        budget = request_budget(a.total, slo)
        print(f"SLI = ({a.total} - {a.bad}) / {a.total} = {sli:.4%}")
        print(f"SLO = {slo:.3%} → {'达标' if sli >= slo else '未达标'}")
        print(f"错误预算 = {a.total} × {1 - slo:.4f} = {budget:.2f} 个请求；已用 {a.bad} 个（{a.bad / budget:.0%}）")
    elif a.cmd == "period":
        slo = pct(a.slo)
        print(f"{a.days:g} 天 × 1440 分钟 × {1 - slo:.4f} = {period_budget_minutes(a.days, slo):.1f} 分钟可不达标")
    elif a.cmd == "burn":
        slo = pct(a.slo)
        hrs = a.interval_days * 24
        bt = burn_threshold(a.budget_pct / 100, hrs, a.window_hours)
        print(f"燃烧率阈值 = {a.budget_pct:g}% × {hrs:g} h / {a.window_hours:g} h = {bt:.2f}")
        print(f"等价错误率阈值 = {bt:.2f} × {1 - slo:.4f} = {error_ratio_threshold(bt, slo):.4%}")
        print(f"若一直以该燃烧率消耗，{hours_to_exhaustion(bt, hrs):.1f} 小时耗尽全部预算")
    else:
        slo = pct(a.slo)
        hrs = a.interval_days * 24
        rows = [("紧急 page", 2, 1, 5 / 60), ("紧急 page", 5, 6, 0.5), ("工单 ticket", 10, 72, 6)]
        print(f"SLO {slo:.3%}，区间 {a.interval_days:g} 天（多窗口、多燃烧率）")
        print(f"{'级别':<10}{'预算%':>6}{'长窗口':>8}{'短窗口':>8}{'燃烧率':>8}{'错误率阈值':>12}")
        for name, budget, long_h, short_h in rows:
            bt = burn_threshold(budget / 100, hrs, long_h)
            print(f"{name:<10}{budget:>6}{long_h:>7g}h{short_h * 60:>7g}m{bt:>8.1f}{error_ratio_threshold(bt, slo):>12.3%}")


if __name__ == "__main__":
    main()
