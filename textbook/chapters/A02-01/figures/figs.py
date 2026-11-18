"""A02-01（第 03 讲）figures."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE

# ---------------------------------------------------------------- 图 3-1 实验拓扑
f = Fig(760, 380)
f.group(8, 8, 744, 364, "AWS Cloud · us-east-1", "cloud", size=10.5)
f.group(22, 38, 600, 326, "VPC 10.20.0.0/16（单 AZ 教学拓扑）", "vpc", size=10.5)
f.group(40, 78, 250, 230, "公有子网 10.20.1.0/24", "public", size=10)
f.group(330, 78, 276, 230, "私有子网 10.20.2.0/24", "private", size=10)
f.box(62, 116, 120, 52, "Client", ["10.20.1.15", "无公网 IP"], "white", title_size=11, size=9.4)
f.box(352, 116, 126, 52, "Server :8080", ["10.20.2.20", "systemd http.server"], "white", title_size=11, size=9.4)
f.box(490, 116, 104, 52, "EIC 端点", ["私网 SSH 入口", "无小时费"], "purple", title_size=10.5, size=9)
f.box(56, 222, 220, 72, "rt-public", ["10.20.0.0/16 → local", "0.0.0.0/0 → igw"], "teal", title_size=10.5, size=9.4)
f.box(346, 222, 130, 72, "rt-private", ["10.20.0.0/16 → local", "（无 0.0.0.0/0）"], "teal", title_size=10.5, size=9.4)
f.box(486, 222, 108, 72, "acl-private", ["#90 DENY 8080（故障）", "#100 ALLOW …", "* DENY"], "orange", title_size=10.5, size=8.8)
f.arrow((182, 142), (352, 142), color=NAVY, label="TCP 8080", dy=-6, label_size=9.6)
f.box(640, 52, 100, 52, "Internet", ["Gateway"], "navy", title_size=11, size=9.6)
f.arrow((276, 246), (640, 78), color=NAVY, dash=True, via=[(310, 246), (310, 60), (628, 60), (628, 78)], label="0/0 → igw", label_at=0.35, dy=-5, label_size=9.4)
f.box(640, 230, 100, 60, "Amazon S3", ["网关终端节点", "（可选）"], "orange", title_size=10.5, size=9)
f.arrow((411, 294), (690, 290), color=ORANGE, dash=True, via=[(411, 318), (690, 318)], label="S3 前缀列表 pl-… → vpce-…（加在 rt-private）", label_at=0.5, dy=-5, label_size=9.2)
f.text(330, 348, "路由决定“去哪里”，NACL 管子网边界，SG 管实例网卡，监听进程决定“有没有人接”", size=10, color=MUTED, anchor="middle")
f.save("lab-topology.svg")

# ---------------------------------------------------------------- 图 3-2 最长前缀匹配
f = Fig(760, 250)
f.text(24, 24, "rt-private（加上 NAT 后）", size=11, weight=700, color=NAVY)
rows = [("目的地", "目标", "前缀长度"), ("10.20.0.0/16", "local", "/16"), ("10.20.2.0/24", "（假设）eni-…", "/24"), ("0.0.0.0/0", "nat-…", "/0")]
for i, (a, b, c) in enumerate(rows):
    y = 36 + i * 30
    fill = "#eef4f7" if i == 0 else "#ffffff"
    f.rect(24, y, 300, 30, fill=fill, stroke="#d0dbe3", sw=1, r=0)
    f.text(36, y + 20, a, size=10.4, weight=700 if i == 0 else 400, color=NAVY if i == 0 else INK, mono=i > 0)
    f.text(172, y + 20, b, size=10.4, weight=700 if i == 0 else 400, color=NAVY if i == 0 else INK, mono=i > 0)
    f.text(290, y + 20, c, size=10.4, weight=700 if i == 0 else 400, color=NAVY if i == 0 else INK, anchor="middle")
dests = [(160, "10.20.2.20", ["命中 /16、/24、/0", "取最长：/24"], TEAL), (215, "10.20.1.15", ["命中 /16、/0", "取最长：/16 → local"], NAVY)]
f.box(380, 30, 360, 60, None, ["规则：只看目的 IP；在所有“包含它”的路由里，", "选前缀最长（最具体）的一条。端口与协议不参与。"], "gray", size=10.2, align="start")
f.box(380, 110, 170, 58, "目的 10.20.2.20", ["命中 /16、/24、/0", "→ /24（最具体）"], "teal", title_size=10.6, size=9.6)
f.box(570, 110, 170, 58, "目的 8.8.8.8", ["只命中 /0", "→ nat-…"], "orange", title_size=10.6, size=9.6)
f.box(380, 182, 360, 54, None, ["没有 0.0.0.0/0 时，8.8.8.8 一条都不命中 → 没有路可走；", "请求连 NACL 和 SG 都不会到达。"], "red", size=10, align="start")
f.text(24, 186, "local 路由由 VPC 自动维护，覆盖整个", size=9.8, color=MUTED)
f.text(24, 204, "VPC CIDR，不能删除；更具体的路由", size=9.8, color=MUTED)
f.text(24, 222, "可以把子网间流量引向防火墙等中间设备。", size=9.8, color=MUTED)
f.save("longest-prefix.svg")

# ---------------------------------------------------------------- 图 3-3 一次请求的往返检查
f = Fig(760, 300)
cols = [("Client", "SG 出站", "有状态"), ("acl-public", "出站", "目的端口 8080"), ("路由", "最长前缀", "10.20.0.0/16 → local"),
        ("acl-private", "入站", "目的端口 8080"), ("Server", "SG 入站 + 监听", "有状态")]
for i, (t, a, b) in enumerate(cols):
    x = 20 + i * 148
    st = "navy" if i in (0, 4) else ("teal" if i == 2 else "orange")
    f.box(x, 40, 128, 66, t, [a, b], st, title_size=11, size=9.4)
    if i < 4:
        f.arrow((x + 128, 73), (x + 148, 73), color=NAVY, sw=1.5)
f.text(24, 28, "请求：10.20.1.15:49152 → 10.20.2.20:8080（SYN）", size=10.5, weight=700, color=NAVY)
f.text(24, 150, "响应：10.20.2.20:8080 → 10.20.1.15:49152（SYN-ACK）", size=10.5, weight=700, color=RED)
rcols = [("Client", "SG 自动放行", "连接已被跟踪"), ("acl-public", "入站", "目的端口 49152"), ("路由", "local", ""),
         ("acl-private", "出站", "目的端口 49152"), ("Server", "SG 自动放行", "连接已被跟踪")]
for i, (t, a, b) in enumerate(rcols):
    x = 20 + i * 148
    st = "gray" if i in (0, 4) else ("teal" if i == 2 else "red")
    lines = [a, b] if b else [a]
    f.box(x, 162, 128, 66, t, lines, st, title_size=11, size=9.4)
    if i < 4:
        f.arrow((x + 148, 195), (x + 128, 195), color=RED, sw=1.5)
f.text(380, 256, "NACL 无状态：回包要再过一遍两侧 NACL，而且目的端口变成了客户端的临时端口（49152）", size=10.2, color=RED, anchor="middle", weight=600)
f.text(380, 276, "SG 有状态：入站放行了请求，回包自动允许，不看出站规则", size=10, color=MUTED, anchor="middle")
f.save("packet-walk.svg")

# ---------------------------------------------------------------- 图 3-4 NACL 从小到大，第一条匹配即停
f = Fig(760, 210)
rules = [("#90", "DENY  TCP 8080  来自 10.20.1.0/24", "red"), ("#100", "ALLOW  全部流量  0.0.0.0/0", "green"), ("*", "DENY  全部流量（不可删除，API 中编号 32767）", "gray")]
for i, (n, t, st) in enumerate(rules):
    y = 30 + i * 52
    f.box(250, y, 360, 40, None, [f"{n}   {t}"], st, size=10.4, align="start")
f.box(24, 72, 170, 58, "入站包", ["TCP 10.20.1.15 → :8080"], "navy", title_size=11, size=9.6)
f.arrow((194, 100), (250, 50), color=NAVY, label="① 先比 #90", dy=-4, dx=-10, label_size=9.6)
f.check(630, 50, ok=False, size=14)
f.text(648, 54, "命中 → 丢弃，停止", size=10, color=RED, weight=700)
f.text(648, 106, "不再评估", size=10, color=MUTED)
f.text(648, 158, "不再评估", size=10, color=MUTED)
f.text(24, 196, "把 #100 改成别的“允许”规则没有用；必须删除 #90，或给它换一个比 90 更大的编号", size=10, color=NAVY, weight=600)
f.save("nacl-order.svg")

# ---------------------------------------------------------------- 图 3-5 出公网要过的四道门
f = Fig(760, 190)
gates = [("① 路由", ["子网路由表有", "0.0.0.0/0 → igw"]), ("② 公网地址", ["实例有公网 IPv4", "（或弹性 IP）"]),
         ("③ SG / NACL", ["出站与回包", "都被允许"]), ("④ 区域开关", ["VPC Block Public", "Access 未阻断"])]
for i, (t, lines) in enumerate(gates):
    x = 30 + i * 178
    f.box(x, 40, 150, 70, t, lines, "teal", title_size=11.5, size=9.6)
    if i < 3:
        f.arrow((x + 150, 75), (x + 178, 75), color=NAVY, sw=1.5)
f.text(380, 24, "从 VPC 内直接访问互联网（经 IGW）必须同时满足：", size=10.8, color=NAVY, anchor="middle", weight=700)
f.text(380, 140, "私有子网的标准做法是：0.0.0.0/0 → NAT 网关（NAT 自己在公有子网、有弹性 IP）", size=10, color=INK, anchor="middle")
f.text(380, 160, "只访问 S3 / DynamoDB：网关终端节点即可，免 NAT 费用；其他 AWS 服务可用接口终端节点（PrivateLink）", size=10, color=MUTED, anchor="middle")
f.save("internet-gates.svg")

# ---------------------------------------------------------------- 图 3-6 排障分流
f = Fig(760, 262)
f.box(270, 14, 220, 44, "curl 的现象是什么？", [], "navy", title_size=12)
cases = [(20, "超时（timeout）", ["包被静默丢弃：", "路由 / NACL / SG", "（SG 拒绝也是丢弃）"], "orange"),
         (270, "连接被拒绝（refused）", ["包到达了实例，", "但端口没有进程监听", "（或主机防火墙 REJECT）"], "red"),
         (520, "HTTP 4xx / 5xx", ["网络已通，", "问题在应用层"], "purple")]
for x, t, lines, st in cases:
    f.box(x, 92, 220, 84, t, lines, st, title_size=11, size=9.8)
    f.arrow((380, 58), (x + 110, 92), color=NAVY, sw=1.3)
f.box(20, 196, 720, 50, None, ["超时时的检查顺序：源/目的 IP 与端口 → 两端子网的路由表 → 两端子网 NACL（双向、临时端口） →", "两端 SG → 用 Reachability Analyzer 或 VPC 流日志（REJECT 记录）取证；不要先把 SG 改成 0.0.0.0/0"], "gray", size=9.8, align="start")
f.save("triage.svg")
print("A02-01 figures ok")
