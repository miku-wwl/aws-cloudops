"""A05-01（第 10 讲）figures."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE

# ---------------------------------------------------------------- 图 10-1 三个平面
f = Fig(760, 330)
f.box(14, 30, 150, 74, "操作者", ["IAM 用户 / 角色", "SendCommand · StartSession"], "white", title_size=11.5, size=9.4)
f.group(214, 14, 250, 196, "AWS 控制面（区域服务）", "cloud", size=10.5)
f.box(232, 52, 214, 56, "Systems Manager", ["鉴权 · 排队 · 记录命令与执行"], "navy", title_size=11.5, size=9.4)
f.box(232, 128, 100, 66, "CloudTrail", ["记录 API 调用", "不含会话正文"], "gray", title_size=10.5, size=8.8)
f.box(346, 128, 100, 66, "EC2 API", ["Runbook 直接调用", "不经过节点"], "teal", title_size=10.5, size=8.8)
f.arrow((164, 67), (232, 74), "① API（操作者的 IAM）", label_size=8.8, dy=-8)
f.arrow((339, 108), (282, 128), color=MUTED, sw=1.2, dash=True)
f.arrow((339, 108), (396, 128), "Automation", color=TEAL, sw=1.4, label_size=8.6, dx=22, dy=2)
f.group(514, 14, 232, 300, "VPC · 受管节点", "vpc", size=10.5)
f.box(532, 52, 196, 76, "SSM Agent", ["主动向外建连（443）", "注册、心跳、取命令、开会话"], "orange", title_size=11.5, size=9.2)
f.box(532, 146, 196, 54, "实例身份", ["实例配置文件 或 DHMC", "凭证来自 IMDS"], "purple", title_size=10.8, size=9)
f.box(532, 218, 196, 74, "操作系统", ["文档里的命令以 root 运行", "“只读”只是命令的选择，不是沙箱"], "red", title_size=10.8, size=9)
f.arrow((532, 84), (446, 84), "② 出站 443：ssm / ssmmessages", label_size=8.8, color=ORANGE, dy=-8)
f.arrow((630, 128), (630, 146), color=PURPLE, sw=1.2, head="both")
f.arrow((630, 200), (630, 218), color=RED, sw=1.2)
f.rect(560, 298, 140, 14, fill="#fbeceb", stroke="none", r=7)
f.text(630, 309, "安全组：没有任何入站规则", size=9, color=RED, anchor="middle", weight=700)
f.note(14, 226, 470, 88, ["① 操作者能不能下命令：看操作者的 IAM（与节点是否在线无关）",
                          "② 节点能不能收命令：看 Agent、实例身份、出站 443 —— 方向是“节点找服务”",
                          "③ Runbook 的 aws:executeAwsApi 只走控制面：节点离线时盘点照样能做",
                          "审计：CloudTrail 只有 API 记录；会话内容要另配 S3 / CloudWatch Logs"],
       style="gray", size=9.4, title="读图要点")
f.save("planes.svg")

# ---------------------------------------------------------------- 图 10-2 四层前提与症状
f = Fig(760, 268)
layers = [("1  Agent", ["已安装、在运行", "版本决定消息通道（3.3.40.0 起优先 ssmmessages）"], ["未注册，或曾注册后 ConnectionLost"], "orange"),
          ("2  身份", ["实例配置文件含 ssm:UpdateInstanceInformation，", "或 DHMC（IMDSv2、Agent ≥ 3.2.582.0）；凭证都来自 IMDS"], ["未注册", "SendCommand → InvalidInstanceId"], "purple"),
          ("3  网络", ["443 到达 ssm（注册、心跳）", "+ 消息通道 ssmmessages（旧版 Agent 用 ec2messages）"], ["缺 ssm：离线", "只缺消息通道：Online 但命令超时"], "teal"),
          ("4  调用方", ["操作者的 IAM：文档、目标节点、", "会话文档、iam:PassRole"], ["AccessDeniedException", "没有 CommandId"], "navy")]
for i, (t, req, sym, st) in enumerate(layers):
    y = 14 + i * 62
    f.box(14, y, 110, 52, t, [], st, title_size=12)
    f.box(134, y, 360, 52, None, req, "white", size=9.3, align="start")
    f.arrow((494, y + 26), (514, y + 26), color=MUTED, sw=1.2)
    f.box(514, y, 232, 52, None, sym, "red" if i < 3 else "gray", size=9.2, align="start")
f.text(304, 262, "从上往下查：上一层不成立，下一层的现象都没有意义", size=10, color=NAVY, anchor="middle", weight=700)
f.text(630, 262, "失败时看到的现象", size=9.4, color=MUTED, anchor="middle")
f.save("four-layers.svg")

# ---------------------------------------------------------------- 图 10-3 两种网络路径
f = Fig(760, 300)
f.group(14, 14, 360, 272, "公网路径（本章实验）", "public", size=10.5)
f.box(30, 52, 150, 64, "EC2 节点", ["公网 IPv4", "SG 出站 TCP 443"], "orange", title_size=11, size=9.2)
f.box(210, 52, 146, 64, "路由表", ["0.0.0.0/0 → IGW"], "white", title_size=11, size=9.2)
f.arrow((180, 84), (210, 84))
f.box(210, 140, 146, 56, "Internet Gateway", [], "gray", title_size=10.5)
f.arrow((283, 116), (283, 140))
f.box(30, 140, 150, 56, "公网端点", ["ssm.*.amazonaws.com …"], "navy", title_size=10.5, size=9)
f.arrow((210, 168), (180, 168))
f.note(30, 212, 326, 62, ["费用：公网 IPv4 0.005 美元/小时", "风险：0.0.0.0/0:443 也能去任何 HTTPS 网站"], style="orange", size=9.4)
f.group(386, 14, 360, 272, "私网路径（生产推荐）", "private", size=10.5)
f.box(402, 52, 150, 64, "EC2 节点", ["无公网 IP", "SG 出站 443 → 端点 SG"], "orange", title_size=11, size=9.2)
f.box(582, 46, 148, 112, "接口端点", ["ssm", "ssmmessages", "ec2messages（旧 Agent）", "s3 网关端点（Agent 更新）"], "teal", title_size=11, size=9)
f.arrow((552, 84), (582, 84), "私有 DNS", label_size=8.8, dy=-8)
f.box(402, 140, 150, 56, "端点安全组", ["入站 443 ← 节点 SG"], "white", title_size=10.5, size=9)
f.arrow((477, 140), (477, 116), color=MUTED, sw=1.2, dash=True)
f.note(402, 212, 328, 62, ["费用：每个接口端点每个 AZ 0.01 美元/小时 + 流量", "私有 DNS 关掉 → Agent 解析到公网地址 → 不可达"], style="teal", size=9.4)
f.save("network-paths.svg")

# ---------------------------------------------------------------- 图 10-4 命令的生命周期
f = Fig(760, 290)
f.box(14, 20, 150, 62, "API 层就失败", ["没有 CommandId"], "red", title_size=11, size=9.2)
f.lines(89, 104, ["InvalidInstanceId：未注册 /", "Agent 未运行 / 实例已终止", "AccessDeniedException：", "操作者 IAM 不允许"], size=9, anchor="middle", color=INK)
states = [("Pending", 210, "gray"), ("InProgress", 360, "navy"), ("Success", 560, "green")]
for name, x, st in states:
    f.box(x, 30, 120, 42, name, [], st, title_size=11.5)
f.arrow((330, 51), (360, 51))
f.arrow((480, 51), (560, 51), "退出码 0", label_size=9)
f.box(560, 96, 120, 36, "Failed", [], "red", title_size=11)
f.arrow((480, 62), (560, 112), "退出码 ≠ 0", label_size=9, dy=12, dx=-10)
f.box(560, 146, 120, 36, "ExecutionTimedOut", [], "red", title_size=10.5)
f.arrow((440, 72), (560, 162), "超过执行超时", label_size=9, dy=14, dx=-30)
f.box(210, 150, 270, 42, "DeliveryTimedOut / Undeliverable", [], "orange", title_size=11)
f.arrow((270, 72), (300, 150), "Agent 收不到", label_size=9, dx=-26)
f.text(345, 214, "总超时 = --timeout-seconds（送达）+ 文档的 executionTimeout（执行）", size=9.6, color=NAVY, anchor="middle", weight=600)
f.note(210, 228, 470, 52, ["Success 只说明“Agent 收到了、退出码为 0”：不代表业务健康，",
                           "以标签为目标却一台都没匹配到时，命令也会以 Success 结束——要看 TargetCount"],
       style="orange", size=9.4)
f.save("command-lifecycle.svg")

# ---------------------------------------------------------------- 图 10-5 控制变量的故障注入时间线
f = Fig(760, 250)
phases = [("① 基线", 232, "green"), ("② 删除出站 443", 380, "orange"), ("③ 重启实例", 528, "red"), ("④ 恢复出站 443", 676, "green")]
rows = [("PingStatus", ["Online", "Online（旧连接未断）", "ConnectionLost", "Online"]),
        ("diag.sh · Run Command", ["Success", "仍可能 Success", "送不到 / 超时", "Success（同一探针）"]),
        ("inventory.sh · Runbook", ["Success", "Success", "Success（控制面）", "Success"])]
for name, x, st in phases:
    f.box(x - 70, 14, 140, 34, name, [], st, title_size=11)
for j, (label, vals) in enumerate(rows):
    y = 64 + j * 46
    f.text(14, y + 24, label, size=9.6, color=NAVY, weight=700)
    for (name, x, st), v in zip(phases, vals):
        bad = any(k in v for k in ("Lost", "送不到"))
        warn = "旧连接" in v or "仍可能" in v
        f.rect(x - 70, y + 4, 140, 32, fill="#fbeceb" if bad else ("#fdf1e3" if warn else "#eaf5ee"), stroke="none", r=6)
        f.text(x, y + 25, v, size=9.4, color=RED if bad else (ORANGE if warn else GREEN), anchor="middle", weight=600)
f.text(380, 222, "安全组有状态：删除规则不会切断已跟踪的长连接，所以要重启（或等连接自然断开）才能看到故障", size=9.6, color=NAVY, anchor="middle", weight=600)
f.text(380, 241, "每次只改一个变量；恢复后用同一个探针复测，才能把结论归因到“出站 443”", size=9.4, color=MUTED, anchor="middle")
f.save("fault-timeline.svg")
print("A05-01 figures ok")
