"""A07-01（第 13 讲）figures."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE

# ---------------------------------------------------------------- 图 13-1 从“备份”到“可恢复”
f = Fig(760, 250)
stages = [("计划 + 选择 + 角色", ["何时、存哪、留多久", "保护哪个 ARN、谁来执行"], "gray"),
          ("备份作业", ["CREATED → RUNNING", "→ COMPLETED"], "navy"),
          ("恢复点", ["备份库中的一个", "时刻快照（ARN）"], "teal"),
          ("恢复作业", ["按元数据创建", "一个新资源"], "purple"),
          ("数据验证", ["行数 · 金额 · 哈希", "对照恢复点时刻"], "orange"),
          ("业务验证", ["冒烟测试 · 切流", "这一步才结束 RTO"], "green")]
for i, (t, ls, st) in enumerate(stages):
    x = 14 + i * 124
    f.box(x, 30, 112, 80, t, ls, st, title_size=10.2, size=8.6)
    if i < 5:
        f.arrow((x + 112, 70), (x + 124, 70), sw=1.4)
proofs = ["只说明选中了什么", "只说明备份动作完成", "只说明有可恢复的副本", "只说明新资源建好了", "说明数据回到了那个时刻", "说明业务恢复了"]
for i, s in enumerate(proofs):
    x = 14 + i * 124
    f.text(x + 56, 134, s, size=8.8, color=RED if i < 4 else GREEN, anchor="middle", weight=600)
f.rect(14, 160, 732, 76, fill="#f6fafb", stroke="#dbe6ec", sw=1, r=8)
f.text(380, 186, "每一个绿色状态只证明它自己那一步", size=11, color=NAVY, anchor="middle", weight=700)
f.text(380, 208, "Backup COMPLETED ≠ 可恢复；Restore COMPLETED ≠ 数据正确；数据正确 ≠ 业务已恢复", size=10, color=INK, anchor="middle")
f.text(380, 226, "所以验收要分三层写：作业状态、数据比对、业务冒烟——缺哪层，结论就只能写到哪层", size=9.4, color=MUTED, anchor="middle")
f.save("backup-chain.svg")

# ---------------------------------------------------------------- 图 13-2 RPO / RTO 时间线
f = Fig(760, 220)
pts = [("10:00", "最后恢复点", 80), ("10:20", "故障", 230), ("10:35", "启动恢复", 342), ("10:55", "新表就绪", 492), ("11:05", "业务验证通过", 567)]
f.line(40, 110, 720, 110, color=NAVY, sw=2)
for hm, what, x in pts:
    col = RED if what == "故障" else NAVY
    f.circle(x, 110, 6, fill=col, stroke="none")
    f.text(x, 96, hm, size=10.5, color=col, anchor="middle", weight=700)
    f.text(x, 134, what, size=9.6, color=INK, anchor="middle")
f.path("M80 62 V52 H230 V62", stroke=ORANGE, sw=1.6)
f.text(155, 44, "实际数据丢失窗口 20 分钟（对照 RPO）", size=9.8, color=ORANGE, anchor="middle", weight=700)
f.path("M230 158 V168 H567 V158", stroke=TEAL, sw=1.6)
f.text(398, 186, "实际恢复耗时 45 分钟（对照 RTO）", size=9.8, color=TEAL, anchor="middle", weight=700)
f.path("M342 62 V52 H492 V62", stroke=PURPLE, sw=1.4, dash="4 3")
f.text(417, 44, "Restore 作业 20 分钟：只是 RTO 的一部分", size=9.4, color=PURPLE, anchor="middle")
f.text(380, 212, "发现、决策、权限、恢复、验证、切流都算进 RTO；备份频率决定最坏情况下的 RPO", size=9.4, color=MUTED, anchor="middle")
f.save("rpo-rto.svg")

# ---------------------------------------------------------------- 图 13-3 4 → 5 → 4 实验
f = Fig(760, 240)
cols = [("T0 写入基线", ["001 · 100", "002 · 120", "003 · 80", "004 · 50"], "4 条 / 350", "navy"),
        ("T1 备份完成", ["恢复点 ARN", "代表 T1 时刻", "的表状态"], "冻结在 4 条", "teal"),
        ("T2 再写一条", ["001 … 004", "005 · 75"], "源表 5 条 / 425", "orange"),
        ("T3 恢复到新表", ["targetTableName", "= …-restored-…"], "新表 4 条 / 350", "purple"),
        ("T4 独立验证", ["行数 4 ✓", "金额 350 ✓", "哈希 = 基线 ✓", "无 005 ✓"], "数据级恢复通过", "green")]
for i, (t, ls, foot, st) in enumerate(cols):
    x = 14 + i * 150
    f.box(x, 14, 136, 150, t, ls, st, title_size=10.8, size=9.2, valign="top")
    f.text(x + 68, 186, foot, size=10, color=NAVY, anchor="middle", weight=700)
    if i < 4:
        f.arrow((x + 136, 89), (x + 150, 89), sw=1.3)
f.text(380, 222, "恢复表少一条不是失败：比较对象是“恢复点时刻的基线”，不是事故后还在变化的源表", size=10, color=RED, anchor="middle", weight=600)
f.save("four-five-four.svg")

# ---------------------------------------------------------------- 图 13-4 DR 策略光谱
f = Fig(760, 240)
f.text(380, 20, "成本与复杂度 →", size=10, color=MUTED, anchor="middle")
strat = [("备份与恢复", ["异地恢复点", "故障后再部署应用"], "RPO/RTO：小时级", "gray"),
         ("Pilot Light", ["数据持续复制", "核心组件常驻、按需扩容"], "RPO 分钟级 / RTO 数十分钟", "teal"),
         ("Warm Standby", ["缩小规模的完整副本", "一直在运行"], "RPO 秒～分 / RTO 分钟级", "orange"),
         ("多站点 Active/Active", ["多个区域同时服务", "需要处理写冲突"], "RPO/RTO 接近零", "red")]
for i, (t, ls, foot, st) in enumerate(strat):
    x = 14 + i * 186
    f.box(x, 34, 172, 86, t, ls, st, title_size=11, size=9.2)
    f.text(x + 86, 140, foot, size=9.4, color=NAVY, anchor="middle", weight=600)
f.note(14, 160, 732, 70, ["只把恢复点复制到另一个区域，还缺：目标区域的网络、IAM、KMS 密钥（跨区恢复要多区域密钥）、Secrets 等机密、",
                          "镜像、服务配额，以及数据库连接、证书、DNS / 负载均衡切换、监控与回切流程。",
                          "图中的量级只是常见范围：真实的 RPO / RTO 只能由演练测量得出。"], style="orange", size=9.4, title="异地副本 ≠ 可运行的备用业务")
f.save("dr-spectrum.svg")
print("A07-01 figures ok")
