"""FIN-01（第 19 讲）figures."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE, LINE

# ---------------------------------------------------------------- 图 19-1 两只时钟
f = Fig(760, 250)
f.text(14, 30, "用量时钟（资源在计量）", size=11, color=NAVY, weight=700)
f.text(14, 136, "出账时钟（账单里看得到）", size=11, color=TEAL, weight=700)
x0, x1 = 170, 740


def X(h):  # h：从 10:00 起的小时数，0~40
    return x0 + (x1 - x0) * h / 40


for y in (40, 146):
    f.line(x0, y + 20, x1, y + 20, color=LINE, sw=1.2)
for h, lab, anc in [(0, "10:00–10:40 实验并销毁", "start"), (20, "次日 06:00", "middle"), (38, "7 天后", "middle")]:
    f.line(X(h), 52, X(h), 176, color="#dbe6ec", sw=1.0, dash="3 3")
    f.text(X(h), 196, lab, size=9, color=MUTED, anchor=anc)
f.rect(X(0), 50, max(6, X(0.6667) - X(0)), 20, fill=NAVY, stroke="none", r=3)
f.text(X(0.6667) + 6, 64, "EC2、公网 IPv4、卷、日志写入：40 分钟", size=9, color=NAVY)
f.rect(X(0.6667), 76, X(38) - X(0.6667), 14, fill="#fdf1e3", stroke=ORANGE, sw=1, r=3)
f.text(X(12), 87, "快照与日志存储：销毁后仍在计量（保留 7 天）", size=9, color="#9a5a1c")
f.rect(X(20), 156, 46, 20, fill=TEAL, stroke="none", r=3)
f.text(X(20) + 52, 170, "前一天 40 分钟的用量此时才入账（晚入账 ≠ 新用量）", size=9, color=TEAL)
f.note(14, 210, 732, 32, ["判断“还有没有新费用”，看账单行的 usage_start / usage_end，而不是它第一次出现在账单里的日期（时间轴为示意）。"], style="orange", size=9.6)
f.save("two-clocks.svg")

# ---------------------------------------------------------------- 图 19-2 三个集合
f = Fig(760, 220)
sets = [("A　Terraform 状态", ["本工程管理的对象", "destroy 能删除它们"], "navy", "核查：state 与 destroy 输出"),
        ("B　仍然存在的资源", ["手工快照、日志组、其他 State", "其他区域、其他账户"], "orange", "核查：跨服务、跨区域盘点"),
        ("C　已经发生的用量", ["销毁前的计量", "可能明天才入账"], "teal", "核查：usage 时间段")]
for i, (t, ls, s, chk) in enumerate(sets):
    x = 14 + i * 250
    f.box(x, 20, 232, 92, t, ls, s, title_size=12, size=9.8)
    f.text(x + 116, 134, chk, size=9.6, color=INK, anchor="middle", weight=600)
f.text(380, 172, "destroy 成功  ≠  账户里没有残留  ≠  账单最终为 0", size=12, color=RED, anchor="middle", weight=700)
f.text(380, 196, "A 能删；B 要先确认归属与保留要求再处置；C 删不掉，只能等它入账后核对", size=9.8, color=MUTED, anchor="middle")
f.save("three-sets.svg")

# ---------------------------------------------------------------- 图 19-3 标签到成本的路径
f = Fig(760, 200)
st = [("给资源打标签", ["Project / Owner", "ExpiresOn"], "white"), ("激活成本分摊标签", ["Billing → 成本分摊标签", "（管理账户）"], "navy"),
      ("账单数据处理", ["约每 24 小时刷新", "新标签键可能要等一天"], "gray"), ("按标签查看与过滤", ["Cost Explorer、预算", "Data Exports"], "teal")]
for i, (t, ls, s) in enumerate(st):
    x = 14 + i * 186
    f.box(x, 20, 168, 72, t, ls, s, title_size=11, size=9.2)
    if i < 3:
        f.arrow((x + 168, 56), (x + 186, 56))
f.note(14, 112, 732, 76, ["只有激活之后的用量才按标签归类；激活前的历史可由管理账户“回填”最多 12 个月（每 24 小时一次）。",
                          "并非所有费用都能按资源标签分摊：税费、部分订阅与共享费用会落在“无标签”组里。",
                          "标签中途改名或改值，不会自动重写旧用量的归属。"], style="orange", size=9.6)
f.save("tag-path.svg")

# ---------------------------------------------------------------- 图 19-4 三层成本防线
f = Fig(760, 230)
layers = [("第一层　事前", ["估算（真实单价 × 用量）、审批、最小权限", "TTL 标签与停止条件；默认零资源的代码"], "navy"),
          ("第二层　事中", ["预算告警（实际 + 预测）、预算动作（IAM / SCP / 停止实例）", "成本异常检测——都依赖账单数据，不是实时闸门"], "teal"),
          ("第三层　事后", ["跨服务、跨区域盘点 + 覆盖清单", "等旧用量入账后再复核，才写“已结清”"], "green")]
for i, (t, ls, s) in enumerate(layers):
    y = 14 + i * 70
    f.box(14 + i * 30, y, 672 - i * 30, 60, t, ls, s, title_size=11, size=9.4, align="start")
f.text(380, 224, "预算不是防火墙：20 美元的预算不会在 20.01 美元时自动阻断所有消费", size=10, color=RED, anchor="middle", weight=600)
f.save("defense-layers.svg")
print("FIN-01 figures ok")
