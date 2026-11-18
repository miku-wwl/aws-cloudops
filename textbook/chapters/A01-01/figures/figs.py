"""A01-01（第 02 讲）figures."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE, FAINT

# ---------------------------------------------------------------- 图 2-1 测量点
f = Fig(760, 300)
xs = [(24, "客户端", ["真实用户 / 探针"], "gray"), (178, "入口层", ["API Gateway / ALB", "鉴权 · 限流"], "navy"),
      (332, "Lambda 服务", ["排队 · 并发配额"], "navy"), (486, "函数代码", ["handler 执行"], "teal"),
      (640, "依赖", ["DynamoDB / RDS"], "orange")]
for x, t, lines, st in xs:
    f.box(x, 40, 100, 70, t, lines, st, title_size=11.5, size=9.4)
for i in range(4):
    f.arrow((xs[i][0] + 100, 75), (xs[i + 1][0], 75), color=NAVY, sw=1.5)
# metric brackets
f.rect(332, 128, 254, 40, fill="#e6f3f3", stroke=TEAL, sw=1, r=6)
f.text(459, 145, "Invocations / Errors / Duration", size=10.2, color="#12676b", anchor="middle", weight=700)
f.text(459, 160, "只覆盖“真正执行了的调用”", size=9.6, color=INK, anchor="middle")
f.rect(332, 176, 100, 40, fill="#fdf1e3", stroke=ORANGE, sw=1, r=6)
f.text(382, 193, "Throttles", size=10.2, color="#9a5a1c", anchor="middle", weight=700)
f.text(382, 208, "执行前被拒绝", size=9.6, color=INK, anchor="middle")
f.rect(178, 176, 140, 40, fill="#f1edf8", stroke=PURPLE, sw=1, r=6)
f.text(248, 193, "入口层 4XX / 5XX", size=10.2, color="#4f3a86", anchor="middle", weight=700)
f.text(248, 208, "函数指标看不到", size=9.6, color=INK, anchor="middle")
f.rect(24, 128, 140, 88, fill="#ecf6f0", stroke=GREEN, sw=1.2, r=6)
f.text(94, 150, "调用方 SLI", size=11, color="#1f5c3d", anchor="middle", weight=700)
f.lines(94, 170, ["成功 / 全部请求", "包含超时、限流、", "入口拒绝"], size=9.6, color=INK)
f.text(380, 250, "同一次“失败”，在不同测量点可能被计入、被漏掉，或被重试掩盖——先定测量点，再谈百分比。", size=10.4, color=NAVY, anchor="middle", weight=600)
f.text(380, 272, "SDK / CLI 默认会对 TooManyRequestsException 重试，调用方看到的成功率可能比函数真实承受的压力更好看", size=9.6, color=MUTED, anchor="middle")
f.save("measure-points.svg")

# ---------------------------------------------------------------- 图 2-2 预算燃烧曲线（斜率 = 燃烧率）
f = Fig(760, 330)
ox, oy, w, h = 70, 270, 600, 220   # origin at (ox, oy), x: 0..30 days, y: 0..100%
f.arrow((ox, oy), (ox + w + 24, oy), color="#7a8b98", sw=1.4)
f.arrow((ox, oy), (ox, oy - h - 20), color="#7a8b98", sw=1.4)
f.text(ox + w + 28, oy + 4, "天", size=10, color=MUTED, anchor="start")
f.text(ox - 8, oy - h - 26, "剩余错误预算", size=10, color=MUTED, anchor="start")
for d in (0, 5, 10, 15, 20, 25, 30):
    x = ox + w * d / 30
    f.line(x, oy, x, oy + 5, color="#7a8b98")
    f.text(x, oy + 18, str(d), size=9.6, color=MUTED, anchor="middle")
for p in (0, 50, 100):
    y = oy - h * p / 100
    f.line(ox - 5, y, ox, y, color="#7a8b98")
    f.text(ox - 9, y + 3.5, f"{p}%", size=9.6, color=MUTED, anchor="end")
    if p:
        f.line(ox, y, ox + w, y, color="#e3eaef", sw=1)
lines = [(1, "燃烧率 1：区间结束时刚好用完", TEAL), (6, "燃烧率 6：5 天用完", ORANGE), (14.4, "燃烧率 14.4：约 2.1 天用完", RED)]
for burn, label, col in lines:
    days = 30 / burn
    x2 = ox + w * days / 30
    f.path(f"M{ox} {oy - h} L{x2} {oy}", stroke=col, sw=2.4)
f.text(ox + w * 0.60, oy - h * 0.40 - 10, "燃烧率 1：第 30 天恰好用完", size=10, color=TEAL, anchor="start", weight=600)
f.text(ox + w * 5 / 30 + 8, oy - 20, "燃烧率 6：5 天用完", size=10, color=ORANGE, anchor="start", weight=600)
f.text(ox + 84, oy - 62, "燃烧率 14.4：约 2.1 天（50 小时）用完", size=10, color=RED, anchor="start", weight=600)
f.rect(ox + 300, oy - h - 4, 300, 62, fill="#f5f8fa", stroke="#d9e3ea", sw=1, r=6)
f.text(ox + 312, oy - h + 16, "读图：直线斜率就是燃烧率", size=10.5, color=NAVY, weight=700)
f.text(ox + 312, oy - h + 34, "燃烧率 = 窗口错误率 ÷ (1 − SLO)", size=10, color=INK)
f.text(ox + 312, oy - h + 50, "耗尽时间 = 区间长度 ÷ 燃烧率", size=10, color=INK)
f.text(380, 316, "SLO 99.9%、30 天区间：允许的失败率是 0.1%；以 1.44% 的失败率持续运行，预算 50 小时就会耗尽", size=9.8, color=MUTED, anchor="middle")
f.save("budget-burn.svg")

# ---------------------------------------------------------------- 图 2-3 多窗口告警逻辑
f = Fig(760, 250)
f.box(24, 30, 170, 64, "长窗口 1 小时", ["失败率 > 1.44% ？", "证明“问题够严重”"], "navy", title_size=11.5, size=9.6)
f.box(24, 120, 170, 64, "短窗口 5 分钟", ["失败率 > 1.44% ？", "证明“问题还在发生”"], "teal", title_size=11.5, size=9.6)
f.box(270, 75, 110, 64, "AND", ["两者同时 ALARM"], "white", title_size=14, size=9.6)
f.arrow((194, 62), (270, 98), color=NAVY)
f.arrow((194, 152), (270, 118), color=TEAL)
f.box(24, 196, 356, 44, None, ["6 小时 / 30 分钟、燃烧率 6（0.6%）的组合同理，两组之间是 OR"], "gray", size=9.8)
f.box(450, 75, 130, 64, "复合告警", ["slo-page", "→ 呼叫值班"], "solid-red", title_size=12, size=9.8)
f.arrow((380, 107), (450, 107), color=RED, sw=1.8)
f.note(600, 24, 148, 202, ["只看长窗口：", "故障已恢复，", "告警还要再响", "近一小时。", "", "只看短窗口：", "一阵抖动就呼人，", "噪声大。", "", "两者相与：", "既灵敏，又能", "及时复位。"], style="orange", size=9.8, title="为什么要两个窗口")
f.save("multiwindow.svg")

# ---------------------------------------------------------------- 图 2-4 故障域
f = Fig(760, 300)
f.group(14, 14, 360, 272, "方案 A：自管 EC2（单 AZ）", "dashed", size=11)
f.group(30, 50, 328, 160, "可用区 us-east-1a", "az", size=10.5)
f.box(48, 92, 130, 56, "EC2 × 2", ["同一可用区"], "white", size=9.6)
f.box(204, 92, 136, 56, "数据库（单 AZ）", ["本地状态"], "orange", size=9.6)
f.arrow((178, 120), (204, 120), color=NAVY)
f.text(194, 238, "两台实例 ≠ 两个故障域：一个 AZ 出问题，全部不可用", size=10, color=RED, anchor="middle", weight=600)
f.text(194, 258, "冗余必须跨越你要防御的那一层边界", size=9.8, color=MUTED, anchor="middle")
f.group(386, 14, 360, 272, "方案 B：区域级托管服务", "dashed", size=11)
f.group(400, 46, 332, 150, "区域 us-east-1", "region", size=10.5)
for i, az in enumerate(("1a", "1b", "1c")):
    x = 414 + i * 106
    f.group(x, 76, 96, 108, f"AZ {az}", "az", size=9.6)
    f.box(x + 10, 110, 76, 30, None, ["Lambda 执行环境"], "teal", size=8.8)
    f.box(x + 10, 146, 76, 30, None, ["DynamoDB 副本"], "orange", size=8.8)
f.text(566, 222, "Lambda、DynamoDB 由 AWS 自动跨多个 AZ 运行", size=10, color=GREEN, anchor="middle", weight=600)
f.text(566, 242, "但你的“依赖”与“配额”仍可能是单点：", size=9.8, color=MUTED, anchor="middle")
f.text(566, 260, "单 AZ 的 RDS、只配一个子网的 VPC 函数、并发配额 10", size=9.8, color=MUTED, anchor="middle")
f.save("fault-domains.svg")

# ---------------------------------------------------------------- 图 2-5 实验闭环
f = Fig(760, 250)
steps = [("① 稳态假设", ["探针 SLI ≥ 99.9%", "告警为 OK"], "navy"),
         ("② 注入故障", ["FAIL_RATE = 0.2", "或 FIS 50% 错误"], "orange"),
         ("③ 观测", ["Errors / Throttles", "燃烧率告警"], "teal"),
         ("④ 停止 / 恢复", ["停止条件触发", "重新 plan 回滚"], "red"),
         ("⑤ 复盘", ["假设是否成立？", "告警是否及时？"], "purple")]
for i, (t, lines, st) in enumerate(steps):
    x = 20 + i * 148
    f.box(x, 50, 130, 76, t, lines, st, title_size=11.5, size=9.6)
    if i < 4:
        f.arrow((x + 130, 88), (x + 148, 88), color=NAVY, sw=1.5)
f.arrow((675, 126), (85, 126), color=MUTED, dash=True, via=[(675, 170), (85, 170)], label="把发现写回设计与 Runbook，再进入下一轮", label_at=0.5, dy=-6, label_size=10)
f.text(380, 215, "护栏：只在实验账户执行；限定目标与比例；设置停止条件；提前确认回滚路径", size=10, color=RED, anchor="middle", weight=600)
f.text(380, 236, "实验证明的是“我们能发现并恢复这一类故障”，而不是“系统已经可靠”", size=9.8, color=MUTED, anchor="middle")
f.save("experiment-loop.svg")
print("A01-01 figures ok")
