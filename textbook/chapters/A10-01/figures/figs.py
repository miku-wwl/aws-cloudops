"""A10-01（第 17 讲）figures."""
import math

from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE, LINE

# ---------------------------------------------------------------- 图 17-1 全互联与枢纽
f = Fig(760, 250)
f.text(190, 22, "VPC Peering 全互联", size=12, color=NAVY, anchor="middle", weight=700)
f.text(570, 22, "Transit Gateway 枢纽", size=12, color=NAVY, anchor="middle", weight=700)
names = ["A", "B", "C", "D", "E"]


def ring(cx, cy, r):
    return [(cx + r * math.sin(2 * math.pi * i / 5), cy - r * math.cos(2 * math.pi * i / 5)) for i in range(5)]


left = ring(190, 118, 70)
for i in range(5):
    for j in range(i + 1, 5):
        f.line(*left[i], *left[j], color=LINE, sw=1.2)
for (x, y), n in zip(left, names):
    f.circle(x, y, 17, fill="#e9eff5", stroke=NAVY, sw=1.4)
    f.text(x, y + 5, n, size=12, color=NAVY, anchor="middle", weight=700)
f.text(190, 222, "连接数 = n(n−1)/2 = 5×4/2 = 10", size=10.5, color=INK, anchor="middle", weight=600)

right = ring(570, 118, 78)
f.rect(540, 100, 60, 36, fill="#fdf1e3", stroke=ORANGE, sw=1.4, r=8)
f.text(570, 123, "TGW", size=12, color="#9a5a1c", anchor="middle", weight=700)
for (x, y), n in zip(right, names):
    f.line(570, 118, x, y, color=ORANGE, sw=1.4)
    f.circle(x, y, 17, fill="#e9eff5", stroke=NAVY, sw=1.4)
    f.text(x, y + 5, n, size=12, color=NAVY, anchor="middle", weight=700)
f.rect(540, 100, 60, 36, fill="#fdf1e3", stroke=ORANGE, sw=1.4, r=8)
f.text(570, 123, "TGW", size=12, color="#9a5a1c", anchor="middle", weight=700)
f.text(570, 222, "附件数 = n = 5；每个附件 0.05 美元/小时", size=10.5, color=INK, anchor="middle", weight=600)
f.line(380, 40, 380, 230, color="#dbe6ec", sw=1.2)
f.text(380, 244, "Peering 不传递：A–B、B–C 都通，A 也到不了 C", size=9.6, color=RED, anchor="middle")
f.save("mesh-vs-hub.svg")

# ---------------------------------------------------------------- 图 17-2 两张表、两个方向
f = Fig(760, 300)
f.text(14, 22, "去程：app → 本地数据库", size=11, color=NAVY, weight=700)
f.box(14, 34, 150, 58, "app 附件", ["关联：spoke 表"], "navy", title_size=11, size=9.6)
f.box(206, 34, 210, 58, "spoke 表", ["172.16.0.0/16 → VPN 附件", "（传播自 VPN 附件）"], "orange", title_size=11, size=9.4)
f.box(458, 34, 130, 58, "VPN 附件", ["隧道 + BGP"], "white", title_size=11, size=9.6)
f.box(630, 34, 116, 58, "本地数据库", ["172.16.20.10"], "gray", title_size=11, size=9.4)
f.arrow((164, 63), (206, 63))
f.arrow((416, 63), (458, 63))
f.arrow((588, 63), (630, 63))
f.text(14, 132, "回程：数据库 → app（另一次查表）", size=11, color=TEAL, weight=700)
f.box(630, 144, 116, 58, "本地路由器", ["10.10/16 → VPN"], "gray", title_size=11, size=9.4)
f.box(458, 144, 130, 58, "VPN 附件", ["关联：hybrid 表"], "navy", title_size=11, size=9.6)
f.box(206, 144, 210, 58, "hybrid 表", ["10.10.0.0/16 → app 附件", "（传播自 app 附件）"], "teal", title_size=11, size=9.4)
f.box(14, 144, 150, 58, "app 子网", ["VPC local 送达"], "white", title_size=11, size=9.6)
f.arrow((630, 173), (588, 173), color=TEAL)
f.arrow((458, 173), (416, 173), color=TEAL)
f.arrow((206, 173), (164, 173), color=TEAL)
f.note(14, 222, 732, 66, ["关联（association）：从这个附件进入 TGW 的流量查哪张表——一个附件只能关联一张。",
                          "传播（propagation）：附件的前缀装进哪些表——可以多张。两者都不会改 VPC 子网路由和本地路由。",
                          "同一前缀：静态 > 系统（1:1 NAT）> 前缀列表 > VPC 传播 > DX > Connect > VPN；先比前缀长度。"],
       style="orange", size=9.4)
f.save("two-tables.svg")

# ---------------------------------------------------------------- 图 17-3 证据阶梯
f = Fig(760, 250)
steps = [("隧道 UP", "IKE/IPsec 建立"), ("BGP 学到前缀", "172.16/16 已收到"), ("TGW 表有路由", "关联表里有前缀"),
         ("子网路由", "172.16/16 → TGW"), ("本地回程", "10.10/16 → VPN"), ("安全控制", "SG/NACL/防火墙"),
         ("TCP 握手", "5432 在监听"), ("业务成功", "认证 + 查询")]
for i, (t, s) in enumerate(steps):
    x, y = 14 + i * 92, 168 - i * 18
    col = GREEN if i == 7 else (NAVY if i < 3 else TEAL)
    f.rect(x, y, 80, 52, fill="#ffffff", stroke=col, sw=1.4, r=7)
    f.text(x + 40, y + 21, t, size=10, color=col, anchor="middle", weight=700)
    f.text(x + 40, y + 38, s, size=8.4, color=INK, anchor="middle")
    if i < 7:
        f.text(x + 86, y + 22, "≠", size=11, color=RED, anchor="middle", weight=800)
f.text(14, 34, "每一级只证明它自己：控制台里 “Tunnel UP” 只是第一级", size=11, color=NAVY, weight=700)
f.text(14, 54, "排障从下往上逐级取证；修复后用同一来源、同一目标、同一端口复验", size=9.8, color=MUTED)
f.save("evidence-ladder.svg")

# ---------------------------------------------------------------- 图 17-4 DNS 的两个方向
f = Fig(760, 300)
f.text(14, 22, "AWS → 本地：Outbound 端点 + 转发规则", size=11, color=NAVY, weight=700)
f.box(14, 34, 118, 58, "工作负载", ["db.corp.example"], "white", title_size=10.5, size=9.2)
f.box(162, 34, 150, 58, "VPC Resolver", ["规则：corp.example", "→ FORWARD"], "navy", title_size=10.5, size=9.2)
f.box(342, 34, 134, 58, "Outbound 端点", ["两个 AZ 的网卡"], "orange", title_size=10.5, size=9.2)
f.box(506, 34, 90, 58, "VPN / DX", ["路由 + 回程"], "gray", title_size=10.5, size=9.2)
f.box(626, 34, 120, 58, "本地 DNS", ["172.16.0.53"], "gray", title_size=10.5, size=9.2)
for a, b in [(132, 162), (312, 342), (476, 506), (596, 626)]:
    f.arrow((a, 63), (b, 63))
f.text(14, 132, "本地 → AWS：本地条件转发 + Inbound 端点", size=11, color=TEAL, weight=700)
f.box(626, 144, 120, 58, "本地客户端", ["app.aws.example"], "white", title_size=10.5, size=9.2)
f.box(476, 144, 120, 58, "本地 DNS", ["aws.example →", "Inbound IP"], "gray", title_size=10.5, size=9.2)
f.box(356, 144, 90, 58, "VPN / DX", ["路由 + 回程"], "gray", title_size=10.5, size=9.2)
f.box(196, 144, 130, 58, "Inbound 端点", ["两个 AZ 的网卡"], "orange", title_size=10.5, size=9.2)
f.box(14, 144, 152, 58, "VPC Resolver", ["私有托管区", "aws.example"], "teal", title_size=10.5, size=9.2)
for a, b in [(626, 596), (476, 446), (356, 326), (196, 166)]:
    f.arrow((a, 173), (b, 173), color=TEAL)
f.note(14, 222, 732, 66, ["规则按最长域名匹配；同一域名上，转发规则优先于自动定义的规则；“.” 由内置的 Internet Resolver 兜底。",
                          "端点安全组要放行 UDP 与 TCP 53；端点按网卡计费（0.125 美元/网卡·小时），每个端点至少两个网卡。",
                          "DNS 通只证明名字解析成功；拿到 IP 之后的 TCP 路径要另外验证（图 17-3）。"],
       style="orange", size=9.4)
f.save("dns-directions.svg")
print("A10-01 figures ok")
