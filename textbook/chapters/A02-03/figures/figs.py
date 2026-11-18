"""A02-03（第 05 讲）figures."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE

# ---------------------------------------------------------------- 图 5-1 一次 API 调用的五道门
f = Fig(760, 300)
layers = [("① DNS", ["域名 → IP"], ["getaddrinfo 失败", "NXDOMAIN"], "navy"),
          ("② 网络", ["路由 + NACL", "+ 两端 SG"], ["连接超时", "（静默丢包）"], "teal"),
          ("③ TLS", ["证书与主机名", "是否匹配"], ["证书 / 主机名", "校验错误"], "purple"),
          ("④ HTTP", ["服务返回", "状态码"], ["任何 HTTP 码", "都说明已到达服务"], "gray"),
          ("⑤ 授权", ["IAM + 终端节点", "策略 + 资源策略"], ["AccessDenied", "HTTP 403"], "orange")]
for i, (t, what, sym, st) in enumerate(layers):
    x = 16 + i * 148
    f.box(x, 40, 132, 70, t, what, st, title_size=12, size=9.4)
    f.rect(x, 120, 132, 64, fill="#fbeceb" if i != 3 else "#ecf6f0", stroke="#e2c7c5" if i != 3 else "#9ccbb0", sw=0.9, r=6)
    f.text(x + 66, 140, "失败时的样子" if i != 3 else "成功的标志", size=9.2, color="#8e2f2c" if i != 3 else GREEN, anchor="middle", weight=700)
    f.lines(x + 66, 158, sym, size=9.2, color=INK, lh=14)
    if i < 4:
        f.arrow((x + 132, 75), (x + 148, 75), color=NAVY, sw=1.5)
f.text(380, 24, "前一层成功，不代表后一层成功：要按层取证，并且一次只改变一个变量", size=10.6, color=NAVY, anchor="middle", weight=700)
f.box(16, 206, 728, 76, None, ["nslookup 成功 ≠ TCP 能建连；TCP 能建连 ≠ TLS 正常；TLS 正常 ≠ 有权限。",
                               "超时几乎总是网络层（②）的问题：先查客户端出站、终端节点 SG 入站、NACL，而不是 DNS 或 IAM；",
                               "得到 AccessDenied 说明网络已通，此时放开安全组毫无用处。"], "gray", size=9.8, align="start")
f.save("five-gates.svg")

# ---------------------------------------------------------------- 图 5-2 VPC 内的 DNS
f = Fig(760, 290)
f.group(14, 14, 470, 262, "VPC 10.42.0.0/16", "vpc", size=10.5)
f.box(34, 60, 140, 60, "Lambda / 实例", ["发起 DNS 查询"], "white", title_size=11, size=9.4)
f.box(230, 52, 236, 76, "Route 53 Resolver", ["地址：VPC 网段 +2（10.42.0.2）", "或 169.254.169.253", "需要 enableDnsSupport = true"], "navy", title_size=11.5, size=9.2)
f.arrow((174, 90), (230, 90), color=NAVY, label="UDP/TCP 53", dy=-6, label_size=9.2)
f.box(34, 150, 432, 112, "按顺序查找", ["1. 与本 VPC 关联的私有托管区（含终端节点私有 DNS 的“隐藏私有托管区”）",
                                       "2. VPC 内部名称（ip-10-42-1-15.ec2.internal 等）",
                                       "3. Resolver 规则（转发到本地 DNS，第 17 讲）",
                                       "4. 公共 DNS（递归解析互联网域名）"], "teal", title_size=11, size=9.4, align="start")
f.box(510, 30, 236, 104, "开启私有 DNS 的接口终端节点", ["ssm.us-east-1.amazonaws.com", "→ 10.42.1.x（终端节点网卡）", "VPC 外解析：仍是公网地址", "（同名，不同答案：分割视界）"], "orange", title_size=10.6, size=9.2)
f.box(510, 152, 236, 110, "两个 VPC 属性", ["enableDnsSupport：Resolver 是否工作", "enableDnsHostnames：是否分配", "公共 DNS 主机名", "私有 DNS 要求两者都为 true"], "purple", title_size=10.6, size=9.2)
f.arrow((466, 108), (510, 90), color=ORANGE, sw=1.3)
f.save("vpc-dns.svg")

# ---------------------------------------------------------------- 图 5-3 网关终端节点 vs 接口终端节点
f = Fig(760, 310)
f.group(14, 14, 360, 282, "网关终端节点（S3 / DynamoDB）", "dashed", size=10.5)
f.box(30, 52, 120, 52, "Lambda", ["10.42.1.15"], "white", title_size=11, size=9.4)
f.box(30, 140, 328, 64, "私有路由表", ["10.42.0.0/16 → local", "pl-63a5400a（S3 前缀列表）→ vpce-…"], "teal", title_size=11, size=9.6)
f.box(222, 52, 136, 52, "Amazon S3", ["公网地址段"], "orange", title_size=11, size=9.4)
f.arrow((150, 78), (222, 78), color=NAVY, label="HTTPS", dy=-6, label_size=9.2)
f.lines(194, 230, ["DNS 照常解析出 S3 的公网地址；", "路由表的前缀列表路由把它送进终端节点。", "没有网卡、没有安全组、不收小时费。"], size=9.6, color=INK)
f.group(386, 14, 360, 282, "接口终端节点（PrivateLink）", "dashed", size=10.5)
f.box(402, 52, 120, 52, "Lambda", ["SG-L：出站 443"], "white", title_size=11, size=9.4)
f.box(598, 52, 132, 52, "终端节点网卡", ["10.42.1.x · SG-E"], "purple", title_size=11, size=9.4)
f.arrow((522, 78), (598, 78), color=NAVY, label="HTTPS 443", dy=-6, label_size=9.2)
f.box(402, 140, 328, 64, "私有 DNS（隐藏私有托管区）", ["ssm.us-east-1.amazonaws.com → 10.42.1.x", "需要 SG-E 入站允许 443 ← SG-L"], "navy", title_size=11, size=9.6)
f.lines(566, 230, ["DNS 把服务域名解析成子网内的私有 IP；", "流量还要通过两端安全组。", "按“每个 AZ 每小时 + 流量”计费。"], size=9.6, color=INK)
f.save("gw-vs-if.svg")

# ---------------------------------------------------------------- 图 5-4 实验拓扑
f = Fig(760, 280)
f.group(14, 14, 560, 252, "VPC 10.42.0.0/16 · 私有子网 10.42.1.0/24 · 单 AZ · 无 NAT / 无 IGW", "vpc", size=10)
f.box(34, 70, 150, 70, "Lambda 探针", ["layers.handler", "SG-L"], "white", title_size=11, size=9.4)
f.box(250, 56, 150, 56, "S3 网关终端节点", ["路由表前缀列表"], "teal", title_size=10.6, size=9.2)
f.box(250, 150, 150, 70, "SSM 接口终端节点", ["私有 DNS · 网卡", "SG-E：443 ← SG-L ?"], "purple", title_size=10.6, size=9.2)
f.arrow((184, 92), (250, 84), color=TEAL, label="mode=s3", dy=-4, label_size=9.2)
f.arrow((184, 118), (250, 180), color=PURPLE, label="mode=ssm", dy=14, dx=-6, label_size=9.2)
f.box(610, 40, 136, 70, "Amazon S3", ["hello.txt", "A05-S3-GATEWAY-OK"], "orange", title_size=10.6, size=9)
f.box(610, 150, 136, 70, "Parameter Store", ["/cloudops/a05/hello", "A05-SSM-INTERFACE-OK"], "orange", title_size=10.6, size=9)
f.arrow((400, 84), (610, 75), color=TEAL)
f.arrow((400, 185), (610, 185), color=PURPLE, dash=True, label="allow_https=false 时被 SG-E 丢弃", dy=-6, label_size=9.2, label_color=RED)
f.text(294, 252, "控制变量：只有 allow_https 一个开关；IAM、DNS、路由在两次实验之间都不变", size=9.8, color=MUTED, anchor="middle")
f.save("lab-topology.svg")
print("A02-03 figures ok")
