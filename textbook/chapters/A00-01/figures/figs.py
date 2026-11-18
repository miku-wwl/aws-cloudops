"""A00-01 figures. Run from this folder (build.py does it automatically)."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, MUTED, PURPLE, INK, GREEN

# ---------------------------------------------------------------- 图 1-1 参考架构
f = Fig(760, 452)
f.group(8, 8, 744, 436, "AWS Organizations 组织", "org")
f.group(22, 42, 716, 96, "管理账户 Management account", "account")
f.box(36, 72, 168, 56, "AWS Control Tower", ["Landing Zone 4.0", "基线 · 控制 · 账户工厂"], "solid-navy", title_size=12, size=10)
f.box(214, 72, 160, 56, "Amazon EventBridge", ["接收 Drift Detected", "（LZ 4.0 起不再用 SNS）"], "orange", title_size=11.5, size=9.6)
f.box(384, 72, 160, 56, "AWS Organizations", ["OU 层级", "SCP / RCP 策略"], "navy", title_size=11.5, size=10)
f.box(554, 72, 170, 56, "IAM Identity Center", ["用户 / 组 → 权限集", "→ 账户（accessManagement）"], "navy", title_size=11.5, size=9.6)
f.arrow((204, 100), (214, 100), color=ORANGE, sw=1.4)

# distribution bus
f.line(120, 128, 120, 150, color=NAVY, sw=1.8)
f.line(120, 150, 690, 150, color=NAVY, sw=1.8)
f.rect(150, 140, 510, 15, fill="#ffffff", stroke="none", r=3)
f.text(405, 151, "下发：集成基线 · OU 基线（EnableBaseline）· 控制（EnableControl / SCP / RCP）", size=9.6, color=NAVY, anchor="middle", weight=600)
for x, y2 in ((300, 162), (520, 196), (690, 196)):
    f.arrow((x, 150), (x, y2), color=NAVY, sw=1.6)

f.group(22, 162, 344, 172, "Security OU（集成账户所在 OU）", "ou")
f.box(34, 204, 104, 100, "Log Archive", ["组织 CloudTrail", "集中日志 S3", "LogArchiveBaseline"], "teal", title_size=11.5, size=9.2)
f.box(148, 204, 104, 100, "Audit", ["SecurityRoles", "跨账户审计角色", "CentralSecurity…"], "teal", title_size=11.5, size=9.2)
f.box(262, 204, 96, 100, "Config 账户", ["服务关联聚合器", "Config 数据桶", "CentralConfig…"], "teal", title_size=11.5, size=9.2)

f.group(380, 162, 358, 172, "Workloads OU", "ou")
f.group(392, 196, 164, 126, "NonProd OU", "dashed", size=10.5)
f.box(404, 224, 140, 50, "payments-nonprod", ["成员账户"], "white", title_size=11, size=9.6)
f.pill(474, 300, "AWSControlTowerBaseline 5.0", fill="#e6f3f3", color="#12676b", size=8.6, anchor="middle")
f.group(566, 196, 160, 126, "Prod OU", "dashed", size=10.5)
f.box(576, 224, 140, 50, "payments-prod", ["成员账户"], "white", title_size=11, size=9.6)
f.pill(646, 300, "基线 + 更严格的控制", fill="#e6f3f3", color="#12676b", size=8.6, anchor="middle")

# audit data flows
f.arrow((524, 322), (86, 304), color=TEAL, dash=True, via=[(524, 388), (86, 388)], label="管理事件 → 组织 Trail → Log Archive 集中日志桶", label_at=0.55, dy=-5, label_size=9.6)
f.arrow((430, 322), (310, 304), color=TEAL, dash=True, via=[(430, 356), (310, 356)], label="配置项 → Config 聚合器", label_at=0.5, dy=-5, label_size=9.6)
f.legend(30, 428, [("治理下发", "arrow:" + NAVY), ("审计数据流", "dash:" + TEAL), ("事件通知", "arrow:" + ORANGE)], size=9.6)
f.save("lz-architecture.svg")

# ---------------------------------------------------------------- 图 1-2 集成依赖
f = Fig(760, 318)
f.text(24, 20, "Landing Zone 级：manifest 字段 → 集成基线", size=11.5, weight=700, color=NAVY)
f.text(470, 20, "OU 级基线：EnableBaseline", size=11.5, weight=700, color=NAVY)
f.box(24, 44, 130, 56, "accessManagement", ["IdentityCenterBaseline"], "navy", title_size=11, size=9.2)
f.box(162, 44, 130, 56, "backup", ["BackupCentralVault", "BackupAdmin"], "orange", title_size=11, size=9.2)
f.box(300, 44, 134, 56, "centralizedLogging", ["LogArchiveBaseline", "（无依赖）"], "gray", title_size=11, size=9.2)
f.box(66, 140, 210, 54, "securityRoles", ["CentralSecurityRolesBaseline"], "teal", title_size=11.5, size=9.6)
f.box(66, 236, 210, 54, "config", ["CentralConfigBaseline（无依赖）"], "teal", title_size=11.5, size=9.6)
f.arrow((89, 100), (130, 140), color=NAVY, label="依赖", dx=-14, dy=-2, label_size=9.6)
f.arrow((227, 100), (212, 140), color=NAVY, label="依赖", dx=16, dy=-2, label_size=9.6)
f.arrow((171, 194), (171, 236), color=NAVY, label="依赖", dx=22, dy=4, label_size=9.6)

f.box(476, 44, 266, 60, "BackupBaseline", ["前提：backup + config 集成", "且该 OU 已启用 AWSControlTowerBaseline"], "orange", title_size=11, size=9.4)
f.box(476, 132, 266, 62, "AWSControlTowerBaseline 5.0", ["注册 OU：Config 记录、审计角色、(IdC 访问)", "前提：config 集成已启用"], "teal", title_size=11, size=9.4)
f.box(476, 228, 266, 62, "ConfigBaseline", ["只部署检测控制所需的 Config 资源", "前提：config 集成已启用"], "teal", title_size=11, size=9.4)
f.arrow((227, 44), (476, 74), color=ORANGE, dash=True, via=[(227, 32), (456, 32), (456, 74)], label="前提", label_at=0.62, dy=-4, label_size=9.6)
f.arrow((276, 263), (476, 163), color=TEAL, dash=True, via=[(440, 263), (440, 163)], label="前提", label_at=0.5, dx=0, dy=-6, label_size=9.6)
f.arrow((440, 259), (476, 259), color=TEAL, dash=True)
f.arrow((609, 104), (609, 132), color=ORANGE, label="同一 OU 须先启用", dx=58, dy=8, label_size=9.4)
f.rect(560, 199, 98, 22, fill="#fbeceb", stroke=RED, sw=1, r=11)
f.text(609, 214, "✕ 同一 OU 二选一", size=9.6, color=RED, anchor="middle", weight=700)
f.legend(24, 312, [("依赖（被依赖者须先启用）", "arrow:" + NAVY), ("启用前提", "dash:" + TEAL)], size=9.6)
f.save("integration-deps.svg")

# ---------------------------------------------------------------- 图 1-3 三种控制行为
f = Fig(760, 262)
f.arrow((24, 150), (742, 150), color="#7a8b98", sw=1.6)
for x, t in ((40, "编写模板"), (300, "提交部署"), (450, "发起 API 请求"), (600, "资源已存在"), (730, "持续运行")):
    f.line(x, 145, x, 155, color="#7a8b98", sw=1.4)
    f.text(x, 170, t, size=9.6, color=MUTED, anchor="middle")
f.box(40, 34, 250, 96, "主动 Proactive · 235 项", ["部署前：CloudFormation Hook", "检查模板里的资源属性", "不合规 → 栈操作失败，资源不创建"], "purple", title_size=11.5, size=9.8)
f.box(300, 34, 200, 96, "预防 Preventive · 69 项", ["请求时：SCP / RCP / 声明式策略", "授权阶段显式 Deny", "动作根本不会发生"], "navy", title_size=11.5, size=9.8)
f.box(510, 34, 226, 96, "检测 Detective · 1309 项", ["发生后：AWS Config 规则", "持续评估已存在的资源", "NON_COMPLIANT → 发现与告警"], "teal", title_size=11.5, size=9.8)
f.text(165, 200, "例：模板中的 S3 桶未开启版本控制", size=9.6, color=INK, anchor="middle")
f.text(165, 218, "→ Hook 返回 FAILED，栈回滚", size=9.6, color=PURPLE, anchor="middle")
f.text(400, 200, "例：成员账户为 root 创建访问密钥", size=9.6, color=INK, anchor="middle")
f.text(400, 218, "→ SCP 显式拒绝 AccessDenied", size=9.6, color=NAVY, anchor="middle")
f.text(623, 200, "例：已有桶被人改成公开可读", size=9.6, color=INK, anchor="middle")
f.text(623, 218, "→ 规则判定不合规，事后发现", size=9.6, color=TEAL, anchor="middle")
f.text(380, 252, "数字为 2026-11-17 Control Catalog（us-east-1）中三种行为的控制数量", size=9, color=MUTED, anchor="middle")
f.save("control-timeline.svg")

# ---------------------------------------------------------------- 图 1-4 预检决策
f = Fig(760, 352)
f.box(24, 14, 280, 40, "① 识别身份", ["`aws sts get-caller-identity`"], "gray", title_size=11, size=9.6)
f.box(24, 86, 280, 50, "② 组织存在吗？", ["`aws organizations describe-organization`"], "orange", title_size=11.5, size=9.6)
f.box(24, 176, 280, 50, "③ 我是管理账户吗？", ["MasterAccountId == 当前 Account ?"], "orange", title_size=11.5, size=9.6)
f.box(24, 266, 280, 50, "④ 已有 Landing Zone 吗？", ["`aws controltower list-landing-zones`"], "orange", title_size=11.5, size=9.6)
f.arrow((164, 54), (164, 86), color=NAVY)
f.arrow((164, 136), (164, 176), color=NAVY, label="存在", dx=20, dy=6, label_size=9.6)
f.arrow((164, 226), (164, 266), color=NAVY, label="是", dx=14, dy=6, label_size=9.6)
f.box(370, 70, 368, 38, None, ["NotInUse → 独立账户：向导第 2 步会新建组织，", "本账户成为管理账户（之后不能更换）"], "white", size=9.6, align="start")
f.box(370, 114, 368, 30, None, ["AccessDenied → 权限不足，不能据此下结论"], "red", size=9.6, align="start")
f.box(370, 182, 368, 38, None, ["否 → 停止：Control Tower 只能在", "组织的管理账户中设置"], "red", size=9.6, align="start")
f.box(370, 254, 368, 38, None, ["有 ARN → get-landing-zone 看版本 / 状态 / 漂移，", "走 Update 流程，绝不重复创建"], "teal", size=9.6, align="start")
f.box(370, 298, 368, 38, None, ["无 → 新建：完整 Landing Zone 向导，", "或在现有组织中“仅启用控制”"], "green", size=9.6, align="start")
f.arrow((304, 104), (370, 89), color=MUTED, sw=1.3)
f.arrow((304, 116), (370, 129), color=RED, sw=1.3)
f.arrow((304, 201), (370, 201), color=RED, sw=1.3, label="否", dy=-5, label_size=9.6)
f.arrow((304, 284), (370, 273), color=TEAL, sw=1.3)
f.arrow((304, 298), (370, 317), color=GREEN, sw=1.3)
f.save("preflight-tree.svg")

# ---------------------------------------------------------------- 图 1-5 验收证据链
f = Fig(760, 238)
cols = [
    ("① Landing Zone", ["get-landing-zone"], "能：版本 / 状态 / 漂移", "不能：成员账户已受治理"),
    ("② manifest", ["线上 manifest"], "能：哪些集成真正启用", "不能：日志已在流入"),
    ("③ 基线", ["list-enabled-baselines", "--include-children"], "能：OU 与子账户的基线", "不能：控制已覆盖风险"),
    ("④ 控制", ["list-enabled-controls"], "能：哪些控制作用于 OU", "不能：没有漏网的风险"),
    ("⑤ 服务证据", ["Trail / Config / IdC"], "能：数据与访问真实存在", "仍需：定期复核与告警"),
]
w, gap, x0 = 136, 10, 22
for i, (t, lines, can, cannot) in enumerate(cols):
    x = x0 + i * (w + gap)
    f.box(x, 18, w, 74, t, lines, "teal" if i < 4 else "navy", title_size=11.5, size=9.4)
    f.rect(x, 108, w, 52, fill="#ecf6f0", stroke="#9ccbb0", sw=0.9, r=6)
    f.text(x + 8, 128, can.split("：")[0] + "：", size=9.2, weight=700, color=GREEN)
    f.text(x + 8, 146, can.split("：")[1], size=9.2, color=INK)
    f.rect(x, 168, w, 52, fill="#fdf3e6", stroke="#ecc59b", sw=0.9, r=6)
    f.text(x + 8, 188, cannot.split("：")[0] + "：", size=9.2, weight=700, color="#9a5a1c")
    f.text(x + 8, 206, cannot.split("：")[1], size=9.2, color=INK)
    if i < 4:
        f.arrow((x + w, 55), (x + w + gap, 55), color=NAVY, sw=1.5)
f.save("evidence-chain.svg")
print("A00-01 figures ok")
