"""A06-02（第 12 讲）figures."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE

# ---------------------------------------------------------------- 图 12-1 谁在看什么
f = Fig(760, 330)
src = [("行为", ["CloudTrail 管理事件", "VPC 流日志 · DNS 查询"], "gray"), ("对象级访问", ["S3 数据事件", "（GuardDuty 自己的数据流）"], "gray"),
       ("工作负载", ["EC2 · ECR 镜像 · Lambda"], "gray"), ("资源配置", ["AWS Config 配置项"], "gray"), ("数据内容", ["S3 中的对象"], "gray")]
eng = [("GuardDuty", ["威胁检测 Finding", "（基础检测）"], "orange"), ("GuardDuty S3 保护", ["可疑的对象读写", "（可选计划）"], "orange"),
       ("Inspector", ["漏洞与网络暴露"], "teal"), ("Security Hub CSPM", ["安全标准与控制"], "navy"), ("Macie", ["敏感数据发现"], "purple")]
for i, ((t1, l1, s1), (t2, l2, s2)) in enumerate(zip(src, eng)):
    y = 14 + i * 60
    f.box(14, y, 176, 50, t1, l1, s1, title_size=10.5, size=8.8)
    f.arrow((190, y + 25), (230, y + 25), color=MUTED, sw=1.2)
    f.box(230, y, 186, 50, t2, l2, s2, title_size=10.5, size=8.8)
    f.arrow((416, y + 25), (470, 160), color=MUTED, sw=1.1)
f.box(470, 110, 150, 100, "Security Hub", ["统一 Finding", "关联成暴露 Finding", "排优先级 · 响应"], "solid-navy", title_size=12, size=9.2)
f.box(640, 110, 108, 100, "响应", ["EventBridge", "工单 / 自动化"], "white", title_size=11, size=9)
f.arrow((620, 160), (640, 160))
f.note(470, 232, 278, 82, ["这些服务只“发现”，不“阻止”：", "数据能不能被读，由 IAM、桶策略、BPA、", "KMS 密钥策略决定（本讲第三、四节）"],
       style="red", size=9.2, title="检测 ≠ 防护")
f.save("signal-map.svg")

# ---------------------------------------------------------------- 图 12-2 SSE-KMS 的两道门
f = Fig(760, 280)
f.box(14, 96, 120, 70, "调用者", ["GetObject", "（HTTPS）"], "white", title_size=11.5, size=9.4)
f.group(170, 20, 250, 230, "第一道门：S3", "private", size=10.5)
f.box(186, 56, 218, 52, None, ["身份策略允许 s3:GetObject？"], "white", size=9.4)
f.box(186, 118, 218, 52, None, ["桶策略没有显式 Deny？", "（非 TLS、TLS < 1.2 …）"], "white", size=9.2)
f.box(186, 180, 218, 52, None, ["公开主体？→ BPA 先拦下"], "white", size=9.4)
f.arrow((134, 131), (170, 131))
f.group(456, 20, 290, 230, "第二道门：KMS（S3 代你调用）", "account", size=10.5)
f.box(472, 56, 258, 52, None, ["密钥状态 Enabled？", "（PendingDeletion / Disabled → 失败）"], "white", size=9.2)
f.box(472, 118, 258, 52, None, ["密钥策略点名了调用者，", "或委托给本账户 IAM（root 语句）？"], "white", size=9.2)
f.box(472, 180, 258, 52, None, ["委托时：身份策略允许 kms:Decrypt？", "（常加 kms:ViaService = s3.<区域>）"], "white", size=9.2)
f.arrow((420, 131), (456, 131), "Decrypt", label_size=9)
f.text(380, 272, "任何一道门不过都返回 403 AccessDenied；写对象时第二道门检查 kms:GenerateDataKey（分段上传还要 kms:Decrypt）", size=9.4, color=NAVY, anchor="middle", weight=600)
f.save("two-gates.svg")

# ---------------------------------------------------------------- 图 12-3 S3 数据保护的层次
f = Fig(760, 250)
layers = [("身份与授权", "IAM 策略 · 桶策略 · KMS 密钥策略", "S3 与 KMS 是两个授权点", NAVY),
          ("公开访问边界", "BPA 四项（账户级 + 桶级 + 访问点）", "取最严格的组合；不替代权限审查", TEAL),
          ("对象所有权", "BucketOwnerEnforced：ACL 失效", "带 ACL 的请求会被拒", PURPLE),
          ("静态加密", "默认 SSE-KMS + Bucket Key；阻止 SSE-C", "只影响新对象；旧对象需另行重加密", ORANGE),
          ("传输加密", "Deny aws:SecureTransport=false · s3:TlsVersion<1.2", "要用负向测试证明它生效", GREEN)]
for i, (t, how, edge, col) in enumerate(layers):
    y = 10 + i * 47
    f.rect(14, y, 150, 40, fill=col, stroke="none", r=6)
    f.text(89, y + 25, t, size=11, color="#ffffff", anchor="middle", weight=700)
    f.rect(170, y, 330, 40, fill="#f6fafb", stroke="#dbe6ec", sw=1, r=6)
    f.text(182, y + 25, how, size=9.6, color=INK)
    f.rect(506, y, 240, 40, fill="#fff8ec", stroke="#f0d5ad", sw=1, r=6)
    f.text(518, y + 25, edge, size=9.4, color="#7a4a14")
f.save("s3-layers.svg")

# ---------------------------------------------------------------- 图 12-4 从 Finding 到结论
f = Fig(760, 250)
steps = [("① 确认信号", "不是 [SAMPLE]；类型、资源、时间"), ("② 确认主体", "用户 / 角色 / 会话、来源 IP"),
         ("③ 还原访问", "事件与对象级记录"), ("④ 数据影响", "读到了什么、读了多少"),
         ("⑤ 受控遏制", "按审批限制会话或路径"), ("⑥ 同一探针复验", "确认被阻止、无新 Finding")]
pos = [(14, 14), (262, 14), (510, 14), (510, 90), (262, 90), (14, 90)]     # 蛇形：上排向右，下排向左
for i, ((t, d), (x, y)) in enumerate(zip(steps, pos)):
    f.box(x, y, 232, 62, t, [d], "navy" if i < 4 else "orange", title_size=11, size=9.2)
f.arrow((246, 45), (262, 45), sw=1.3)
f.arrow((494, 45), (510, 45), sw=1.3)
f.arrow((626, 76), (626, 90), sw=1.3)
f.arrow((510, 121), (494, 121), sw=1.3)
f.arrow((262, 121), (246, 121), sw=1.3)
f.note(14, 172, 732, 70, ["对象级证据从哪里来：GuardDuty S3 保护的 Finding 详情；你自己跟踪中的 S3 数据事件（默认不记录）；",
                          "KMS Decrypt 是管理事件，事件历史里查得到——但开启 Bucket Key 后，加密上下文只到“桶”，",
                          "而且调用次数大幅减少：省钱的同时也降低了 KMS 侧的审计粒度。"], style="gray", size=9.4, title="证据来源")
f.save("investigation.svg")
print("A06-02 figures ok")
