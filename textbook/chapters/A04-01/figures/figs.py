"""A04-01（第 08 讲）figures."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE

# ---------------------------------------------------------------- 图 8-1 指标身份
f = Fig(760, 220)
parts = [("区域", "us-east-1", "gray"), ("命名空间", "Lab/CloudOps", "navy"), ("指标名", "Errors", "teal"),
         ("维度集合（全部）", "Service=checkout", "orange")]
x = 20
for i, (t, v, st) in enumerate(parts):
    w = 150 if i < 3 else 190
    f.box(x, 30, w, 58, t, [f"`{v}`"], st, title_size=11, size=10)
    if i < 3:
        f.text(x + w + 9, 64, "+", size=18, color=MUTED, anchor="middle", weight=700)
    x += w + 18
f.text(380, 116, "四者完全相同，才是同一条时间序列；单位与统计方式在读取时选择", size=10.4, color=NAVY, anchor="middle", weight=600)
f.box(20, 136, 350, 70, None, ["Errors · Service=checkout", "Errors · Service=billing", "Errors · Service=checkout, AZ=us-east-1a"], "white", size=9.8, align="start")
f.box(400, 136, 340, 70, None, ["→ 三条不同的时间序列，CloudWatch 不会替你合并；", "  告警写错一个维度值，就会盯着一条“没有数据”的序列", "  （再配上 notBreaching，就永远是 OK）"], "red", size=9.6, align="start")
f.save("metric-identity.svg")

# ---------------------------------------------------------------- 图 8-2 一条告警的计算链
f = Fig(760, 250)
chain = [("原始数据点", ["PutMetricData", "每次一个值"], "gray"), ("按 Period 聚合", ["Period = 60 秒", "Statistic = Sum"], "teal"),
         ("与阈值比较", ["≥ 1 → 越界 X", "< 1 → 未越界 0"], "navy"), ("M / N 判定", ["最近 N=3 个点中", "≥ M=2 个越界"], "orange"),
         ("状态", ["OK / ALARM /", "INSUFFICIENT_DATA"], "purple")]
for i, (t, lines, st) in enumerate(chain):
    x = 16 + i * 150
    f.box(x, 30, 132, 70, t, lines, st, title_size=11.2, size=9.4)
    if i < 4:
        f.arrow((x + 132, 65), (x + 150, 65), color=NAVY, sw=1.5)
seq = [("T1", "0"), ("T2", "X"), ("T3", "0"), ("T4", "X"), ("T5", "X"), ("T6", "0")]
for i, (t, v) in enumerate(seq):
    x = 110 + i * 70
    col = {"X": RED, "0": GREEN}[v]
    f.rect(x, 140, 52, 40, fill="#fbeceb" if v == "X" else "#ecf6f0", stroke=col, sw=1.2, r=6)
    f.text(x + 26, 166, v, size=14, color=col, anchor="middle", weight=800)
    f.text(x + 26, 196, t, size=9.6, color=MUTED, anchor="middle")
f.rect(240, 132, 200, 74, fill="none", stroke=ORANGE, sw=1.8, r=8, dash="6 4")
f.text(340, 224, "T3–T5 窗口：X 有 2 个 → ALARM（不要求连续）", size=10, color=ORANGE, anchor="middle", weight=600)
f.text(600, 166, "2-of-3 ≠ 连续 2 分钟", size=11, color=NAVY, anchor="start", weight=700)
f.save("alarm-chain.svg")

# ---------------------------------------------------------------- 图 8-3 缺失数据如何补
f = Fig(760, 268)
f.box(20, 20, 220, 64, "① 取“评估范围”的数据点", ["比 N 多取几个（文档示例：N=3 取 5）", "最新的在右边"], "navy", title_size=10.8, size=9.2)
f.box(270, 20, 220, 64, "② 最近 N 个都在？", ["是 → 只看这 N 个", "（缺失处理用不上）"], "teal", title_size=10.8, size=9.2)
f.box(520, 20, 220, 64, "③ 范围内真实点 ≥ N？", ["是 → 用最近 N 个真实点", "（缺失处理仍用不上）"], "teal", title_size=10.8, size=9.2)
f.arrow((240, 52), (270, 52), color=NAVY)
f.arrow((490, 52), (520, 52), color=NAVY, label="否", dy=-6, label_size=9.4)
f.box(270, 110, 470, 64, "④ 真实点不足 N：按 treat_missing_data 补齐", ["notBreaching → 补“好点”；breaching → 补“坏点”；", "missing → 全缺时 INSUFFICIENT_DATA；ignore → 全缺时保持原状态"], "orange", title_size=10.8, size=9.2)
f.arrow((630, 84), (630, 110), color=NAVY, label="否", dx=14, dy=6, label_size=9.4)
f.box(270, 192, 470, 60, "⑤ 过早告警保护（missing / ignore）", ["真实点少于 M 时，只有最早的越界点已至少 M 期“老”、其后全是越界或缺失，", "才判 ALARM（ignore 保持原状态）；否则先等更多数据"], "purple", title_size=10.8, size=9.2)
f.arrow((505, 174), (505, 192), color=NAVY)
f.note(20, 110, 222, 142, ["停发数据后，旧的真实点", "还会在评估范围里被反复", "使用几分钟——", "所以告警不会“立刻”变化。", "", "缩短 Period 可以缩短", "这段“惯性”。"], style="gray", size=9.6, title="为什么停发后有延迟")
f.save("missing-flow.svg")

# ---------------------------------------------------------------- 图 8-4 错误数 vs 错误率
f = Fig(760, 230)
rows = [("低流量", "10", "5", "50%", "错误数告警：触发；错误率告警：触发（严重）", RED),
        ("高流量", "10 000", "5", "0.05%", "错误数告警：触发（噪声）；错误率告警：不触发", ORANGE),
        ("无流量", "0", "0", "无定义", "错误数：OK；错误率：样本不足，交给心跳告警", MUTED)]
heads = ["场景", "Requests", "Errors", "错误率", "两种告警的反应"]
xs = [20, 110, 210, 300, 390]
ws = [90, 100, 90, 90, 350]
for j, h in enumerate(heads):
    f.rect(xs[j], 18, ws[j], 32, fill="#eef4f7", stroke="#c9d6df", sw=1, r=0)
    f.text(xs[j] + 10, 39, h, size=10.4, weight=700, color=NAVY)
for i, (a, b, c, d, e, col) in enumerate(rows):
    y = 50 + i * 40
    for j, cell in enumerate((a, b, c, d, e)):
        f.rect(xs[j], y, ws[j], 40, fill="#ffffff", stroke="#dde6ec", sw=1, r=0)
        f.text(xs[j] + 10, y + 25, cell, size=9.8, color=col if j == 4 else INK, weight=600 if j == 4 else 400)
f.text(380, 200, "错误率 = 100 × Sum(Errors) ÷ Sum(Requests)；再加“最小样本”保护：IF(req ≥ 50, 100*err/req, 0)", size=10, color=NAVY, anchor="middle", weight=600)
f.text(380, 220, "零流量时除法没有意义：指标数学里除以 0 的数据点会被丢弃，零流量要由心跳 / 合成探针另行发现", size=9.6, color=MUTED, anchor="middle")
f.save("count-vs-rate.svg")
print("A04-01 figures ok")
