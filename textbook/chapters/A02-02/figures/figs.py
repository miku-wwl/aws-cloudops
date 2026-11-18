"""A02-02（第 04 讲）figures."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE

# ---------------------------------------------------------------- 图 4-1 网卡上的规则并集
f = Fig(760, 262)
f.box(24, 70, 150, 64, "入站包", ["TCP 来自 10.40.1.10", "目的端口 8080"], "navy", title_size=11.5, size=9.6)
f.group(220, 24, 330, 214, "ENI（实例的网卡）", "plain", size=10.5)
f.box(240, 62, 140, 74, "SG-base", ["22 ← sg-eic", "9100 ← 10.40.0.0/16"], "white", title_size=11, size=9.4)
f.box(392, 62, 140, 74, "SG-app", ["8080 ← sg-client", "（实验开关）"], "white", title_size=11, size=9.4)
f.box(240, 152, 292, 70, "生效规则 ＝ 所有 SG 的允许规则之并集", ["任何一条匹配 → 放行；没有一条匹配 → 静默丢弃", "（没有 Deny 规则，也就不存在“Deny 优先”）"], "teal", title_size=10.6, size=9.4)
f.arrow((174, 102), (240, 102), color=NAVY, sw=1.6)
f.box(596, 40, 146, 82, "来源 = sg-client", ["匹配“挂了 sg-client 的", "网卡的私有 IP”", "不复制对方的规则"], "purple", title_size=10.6, size=9.2)
f.box(596, 140, 146, 82, "配额", ["每块网卡默认 5 个 SG", "每个 SG 每方向 60 条", "（均可申请提高）"], "orange", title_size=10.6, size=9.2)
f.save("sg-union.svg")

# ---------------------------------------------------------------- 图 4-2 连接跟踪时间线
f = Fig(760, 300)
f.text(110, 22, "Client 10.40.1.10:49152", size=10.5, weight=700, color=NAVY, anchor="middle")
f.text(470, 22, "Server 10.40.1.20:8080", size=10.5, weight=700, color=NAVY, anchor="middle")
f.line(110, 30, 110, 190, color="#b8c7d2", sw=1.2, dash="4 4")
f.line(470, 30, 470, 190, color="#b8c7d2", sw=1.2, dash="4 4")
msgs = [(60, "① SYN：新连接，Client 出站 + Server 入站规则都要匹配", 110, 470, NAVY),
        (110, "② SYN-ACK：已跟踪连接的回包，自动放行", 470, 110, GREEN),
        (160, "③ ACK / 数据：同一连接，双向自动放行", 110, 470, GREEN)]
for y, label, x1, x2, col in msgs:
    f.arrow((x1, y), (x2, y), color=col, sw=1.6)
    f.text(290, y - 7, label, size=9.8, color=col, anchor="middle", weight=600)
f.box(520, 40, 226, 140, "删除 / 收紧规则之后", ["已跟踪的连接：不受影响，", "直到空闲超时才结束", "（TCP 默认 432000 秒；", "Nitro v6 为 350 秒）", "新连接：立即按新规则判断"], "orange", title_size=10.8, size=9.4)
f.box(24, 206, 722, 78, "例外：不被跟踪的流（untracked）", ["入站对 0.0.0.0/0（或 ::/0）放行某 TCP/UDP 流，且出站对全网放行全部端口时，该流不被跟踪；", "回包靠反方向的规则放行。删除这类规则会立刻切断现有连接。ICMP 总是被跟踪；", "经 NAT 网关、NLB、接口终端节点、Lambda Hyperplane ENI 等的连接会被自动跟踪。"], "gray", title_size=10.8, size=9.4, align="start")
f.save("conntrack.svg")

# ---------------------------------------------------------------- 图 4-3 三层安全组链
f = Fig(760, 250)
f.box(16, 80, 120, 70, "办公网", ["前缀列表", "pl-office"], "gray", title_size=11, size=9.4)
f.box(186, 80, 120, 70, "sg-web", ["入：443", "← pl-office"], "navy", title_size=11.5, size=9.4)
f.box(356, 80, 120, 70, "sg-app", ["入：8080", "← sg-web"], "teal", title_size=11.5, size=9.4)
f.box(526, 80, 120, 70, "sg-db", ["入：5432", "← sg-app"], "orange", title_size=11.5, size=9.4)
f.arrow((136, 115), (186, 115), color=NAVY, label="443", dy=-6, label_size=9.6)
f.arrow((306, 115), (356, 115), color=NAVY, label="8080", dy=-6, label_size=9.6)
f.arrow((476, 115), (526, 115), color=NAVY, label="5432", dy=-6, label_size=9.6)
f.box(660, 40, 90, 60, "Amazon S3", ["前缀列表", "pl-63a5400a"], "gray", title_size=10, size=8.8)
f.arrow((440, 80), (660, 70), color=TEAL, dash=True, via=[(440, 58), (640, 58)], label="app 出：443 → S3 前缀列表", label_at=0.5, dy=-5, label_size=9.4)
f.text(380, 186, "每一层只信任上一层的“身份”（SG），而不是某段 IP：实例扩缩容、换 IP，规则都不用改", size=10.2, color=NAVY, anchor="middle", weight=600)
f.text(380, 206, "出站也按需收紧：web 只能去 app:8080，app 只能去 db:5432 与 S3:443，db 没有任何出站规则", size=9.8, color=MUTED, anchor="middle")
f.text(380, 226, "db 的回包仍能返回 app——靠的是连接跟踪，而不是出站规则", size=9.8, color=MUTED, anchor="middle")
f.save("tier-chain.svg")

# ---------------------------------------------------------------- 图 4-4 SG 引用的适用范围
f = Fig(760, 236)
rows = [("同一个 VPC", "✓", "✓", "最常用：app ← sg-web"),
        ("VPC 对等连接（同区域）", "✓", "✓", "跨 VPC 引用对方 SG；删除对等后规则变为 stale"),
        ("Transit Gateway", "✓", "✗", "仅入站规则可引用（TGW 需开启 SG 引用支持）"),
        ("经中间设备（防火墙）转发", "✗", "✗", "必须改用对端私有 IP 或子网 CIDR")]
head = ["场景", "入站规则可引用", "出站规则可引用", "说明"]
xs = [24, 220, 340, 460]
ws = [196, 120, 120, 276]
for j, h in enumerate(head):
    f.rect(xs[j], 20, ws[j], 32, fill="#eef4f7", stroke="#c9d6df", sw=1, r=0)
    f.text(xs[j] + 10, 41, h, size=10.4, weight=700, color=NAVY)
for i, row in enumerate(rows):
    y = 52 + i * 42
    for j, cell in enumerate(row):
        f.rect(xs[j], y, ws[j], 42, fill="#ffffff", stroke="#dde6ec", sw=1, r=0)
        if cell in ("✓", "✗"):
            f.check(xs[j] + ws[j] / 2, y + 21, ok=(cell == "✓"), size=13)
        else:
            f.text(xs[j] + 10, y + 26, cell, size=9.8, color=INK)
f.text(380, 230, "依据：AWS VPC 用户指南《Security group referencing》（2026-11-17 核对）", size=9, color=MUTED, anchor="middle")
f.save("ref-scope.svg")
print("A02-02 figures ok")
