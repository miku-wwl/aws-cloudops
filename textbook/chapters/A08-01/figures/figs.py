"""A08-01（第 14 讲）figures."""
import json
from pathlib import Path

from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE

# ---------------------------------------------------------------- 图 14-1 事故响应与复盘
f = Fig(760, 250)
steps = [("发现", ["告警 / 用户报告", "外部探针"], "gray"), ("分诊", ["影响多大？", "要不要升级？"], "navy"),
         ("止损恢复", ["最小、可回滚", "同探针复验"], "orange"), ("复盘 RCA", ["为什么会发生", "为什么没早发现"], "purple"),
         ("行动项", ["负责人 · 期限", "验收标准"], "green")]
for i, (t, ls, st) in enumerate(steps):
    x = 14 + i * 150
    f.box(x, 20, 134, 70, t, ls, st, title_size=11.5, size=9)
    if i < 4:
        f.arrow((x + 134, 55), (x + 150, 55))
f.text(160, 112, "事故响应：恢复到已知可用状态", size=10, color=ORANGE, anchor="middle", weight=700)
f.text(540, 112, "根因分析：有证据的原因 + 可验收的改进", size=10, color=PURPLE, anchor="middle", weight=700)
cols = [("事实", ["CloudTrail 记录了一次成功的 API 调用", "当前规则里没有 TCP 80 /32", "探针结果带 UTC 时间戳"], GREEN),
        ("推断", ["规则缺失可以解释新连接超时", "——要能被反例挑战"], ORANGE),
        ("未知", ["是否所有用户都受影响？", "是否还有同时发生的其他变更？"], RED)]
for i, (t, ls, col) in enumerate(cols):
    x = 14 + i * 248
    f.rect(x, 128, 236, 108, fill="#ffffff", stroke=col, sw=1.3, r=8)
    f.text(x + 12, 150, t, size=11, color=col, weight=800)
    for j, s in enumerate(ls):
        f.text(x + 12, 172 + j * 19, s, size=9.4, color=INK)
f.save("ir-rca.svg")

# ---------------------------------------------------------------- 图 14-2 现象 → 层次
f = Fig(760, 250)
layers = ["DNS", "路由 / IGW", "NACL（无状态）", "安全组（有状态）", "主机防火墙", "进程监听", "应用 / 依赖"]
for i, t in enumerate(layers):
    x = 14 + i * 106
    f.box(x, 20, 98, 46, t, [], "navy" if i < 4 else "teal", title_size=10)
    if i < 6:
        f.arrow((x + 98, 43), (x + 106, 43), sw=1.2)
sym = [("解析失败", 0, 0, RED), ("TCP 超时（包被丢弃或无人应答）", 1, 4, ORANGE), ("连接被拒绝（RST）", 5, 5, PURPLE), ("HTTP 4xx / 5xx", 6, 6, NAVY)]
for k, (t, a, b, col) in enumerate(sym):
    y = 96 + k * 34
    x1, x2 = 14 + a * 106, 14 + b * 106 + 98
    f.rect(x1, y, x2 - x1, 26, fill="#ffffff", stroke=col, sw=1.4, r=13)
    f.text((x1 + x2) / 2, y + 17.5, t, size=9.6, color=col, anchor="middle", weight=700)
f.text(380, 240, "超时只把范围缩小到五层之一：安全组只是其中之一，要逐层排除", size=10, color=NAVY, anchor="middle", weight=600)
f.save("symptom-layers.svg")

# ---------------------------------------------------------------- 图 14-3 鉴别诊断矩阵（来自 labs/01-ir/case.json）
case = json.loads((Path(__file__).resolve().parents[1] / "labs" / "01-ir" / "case.json").read_text(encoding="utf-8"))
obs = case["observations"]
hyps = case["hypotheses"]
f = Fig(760, 300)
f.text(14, 22, "观察 →", size=9.6, color=MUTED)
for j, o in enumerate(obs):
    x = 250 + j * 62
    f.text(x + 26, 22, o["id"], size=10, color=NAVY, anchor="middle", weight=700)
seen = {o["id"]: o["value"] for o in obs}
for i, h in enumerate(hyps):
    y = 36 + i * 36
    alive = not any((p == "+") != bool(seen[k]) for k, p in h["predicts"].items() if p != "0" and k in seen)
    f.rect(14, y, 226, 30, fill="#eaf5ee" if alive else "#fbeceb", stroke="none", r=5)
    f.text(24, y + 20, f"{h['id']} {h['title']}", size=9.4, color=GREEN if alive else RED, weight=700 if alive else 400)
    for j, o in enumerate(obs):
        x = 250 + j * 62
        p = h["predicts"].get(o["id"], "0")
        if p == "0":
            f.text(x + 26, y + 20, "·", size=12, color="#b8c7d2", anchor="middle")
        else:
            ok = (p == "+") == bool(seen[o["id"]])
            f.check(x + 26, y + 19, ok=ok, size=11)
f.text(380, 270, "✓ 观察与预测一致   ✗ 观察与预测矛盾（证伪）   · 该观察与此假设无关", size=9.4, color=MUTED, anchor="middle")
f.text(380, 290, "只有 H1 与所有观察相容；去掉 O7、O8，H4（NACL）就无法排除——证据决定结论能写到多肯定", size=9.6, color=NAVY, anchor="middle", weight=600)
f.save("dx-matrix.svg")

# ---------------------------------------------------------------- 图 14-4 探针时间线与不确定区间
f = Fig(760, 200)
x0, dx = 40, 27
for m in range(0, 26):
    ok = not (7 <= m <= 20)
    x = x0 + m * dx
    f.circle(x, 70, 6, fill=GREEN if ok else RED, stroke="none")
    if m % 2 == 0 or m in (7, 21):
        f.text(x, 96, f"10:{m:02d}", size=8.4, color=MUTED, anchor="middle")
f.line(x0 - 10, 70, x0 + 25 * dx + 10, 70, color="#d0dbe3", sw=1)
f.rect(x0 + 6 * dx, 40, dx, 14, fill="#fdf1e3", stroke="none", r=3)
f.text(x0 + 6.5 * dx, 34, "起点在这里", size=8.8, color=ORANGE, anchor="middle", weight=700)
f.rect(x0 + 20 * dx, 40, dx, 14, fill="#fdf1e3", stroke="none", r=3)
f.text(x0 + 20.5 * dx, 34, "终点在这里", size=8.8, color=ORANGE, anchor="middle", weight=700)
f.arrow((x0 + 12 * dx, 140), (x0 + 12 * dx, 80), color=PURPLE)
f.text(x0 + 12 * dx + 8, 138, "10:12 第一条告警", size=9.2, color=PURPLE, weight=700)
f.text(380, 178, "停机时长 ∈ [10:20 − 10:07, 10:21 − 10:06] = [13, 15] 分钟；检测耗时 = 10:12 − 10:07 = 5 分钟", size=9.8, color=NAVY, anchor="middle", weight=700)
f.save("probe-window.svg")
print("A08-01 figures ok")
