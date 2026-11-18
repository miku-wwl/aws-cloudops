#!/usr/bin/env python3
"""recovery：恢复点的时间语义与 RPO / RTO 计算（第 13 讲实验 13-1，离线、零费用）。

    python recovery.py timeline     # 教材例题：10:00 恢复点、10:20 故障……算出实际 RPO / RTO
    python recovery.py strategies   # 同一次故障，在“每日备份 / 每小时备份 / PITR”下各丢多少数据

定义（与 AWS 一致）：
  RPO（恢复点目标）：可以接受丢失多长时间的数据；实际丢失窗口 = 故障时刻 − 最后一个可用恢复点的时刻
  RTO（恢复时间目标）：从中断到业务恢复可用的最长时间；实际耗时 = 业务验证通过的时刻 − 中断时刻
  DynamoDB 的按需备份 / AWS Backup 恢复点代表“发起备份那一刻”的表状态；
  PITR 可以恢复到保留期（1–35 天，默认 35）内的任意一秒，最新可恢复时间通常比当前时间早约 5 分钟。
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta


def t(s: str) -> datetime:
    return datetime.strptime(s, "%H:%M")


def minutes(a: datetime, b: datetime) -> int:
    return int((b - a).total_seconds() // 60)


def last_recovery_point(failure: datetime, first: datetime, every: timedelta) -> datetime:
    """按固定周期产生的恢复点中，故障前最后一个。"""
    n = (failure - first) // every
    return first + n * every


def timeline() -> None:
    ev = [("10:00", "最后一个恢复点创建"), ("10:20", "故障，服务中断"), ("10:35", "发现并启动恢复"),
          ("10:55", "恢复出的新表 ACTIVE"), ("11:05", "业务冒烟测试通过，切换完成")]
    for hm, what in ev:
        print(f"  {hm}  {what}")
    rp, fail, ok = t("10:00"), t("10:20"), t("11:05")
    print(f"\n  实际数据丢失窗口 = 10:20 − 10:00 = {minutes(rp, fail)} 分钟（对照 RPO）")
    print(f"  实际恢复耗时     = 11:05 − 10:20 = {minutes(fail, ok)} 分钟（对照 RTO）")
    print(f"  其中 Restore 作业 = 10:55 − 10:35 = {minutes(t('10:35'), t('10:55'))} 分钟——它只是 RTO 的一部分")


def strategies() -> None:
    failure = datetime(2026, 11, 17, 14, 30)
    rows = [("每日 05:00（UTC）备份", last_recovery_point(failure, datetime(2026, 11, 1, 5, 0), timedelta(days=1))),
            ("每小时整点备份", last_recovery_point(failure, datetime(2026, 11, 1, 0, 0), timedelta(hours=1))),
            ("PITR（最新可恢复≈故障前 5 分钟）", failure - timedelta(minutes=5))]
    print(f"  故障时刻：{failure:%m-%d %H:%M}")
    for name, rp in rows:
        print(f"  {name:28} 最后恢复点 {rp:%m-%d %H:%M}  → 丢失 {minutes(rp, failure):5d} 分钟")
    print("  最坏情况：每日备份 ≈ 24 小时 + 启动窗口；每小时 ≈ 60 分钟 + 启动窗口；PITR ≈ 数分钟")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["timeline", "strategies"])
    a = ap.parse_args()
    timeline() if a.what == "timeline" else strategies()


if __name__ == "__main__":
    main()
