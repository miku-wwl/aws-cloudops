"""A03-02（第 07 讲）figures."""
from figlib import Fig, seq, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE

# ---------------------------------------------------------------- 图 7-1 三道门
f = Fig(760, 200)
gates = [("联邦身份", ["OIDC 令牌 → STS", "信任策略：aud / sub"], "navy", "失败：AssumeRoleWithWebIdentity 被拒"),
         ("秘密 API", ["secretsmanager:", "GetSecretValue"], "teal", "失败：AccessDenied（未提 KMS）"),
         ("KMS 解密", ["kms:Decrypt", "密钥策略 + IAM"], "orange", "失败：AccessDenied（提到 kms:Decrypt）")]
for i, (t, lines, st, fail) in enumerate(gates):
    x = 30 + i * 250
    f.box(x, 26, 200, 70, t, lines, st, title_size=12, size=9.6)
    f.text(x + 100, 118, fail, size=9.4, color=RED, anchor="middle")
    if i < 2:
        f.arrow((x + 200, 61), (x + 250, 61), color=NAVY, sw=1.6)
f.box(30, 140, 700, 48, None, ["身份成功 ≠ 有权调用 API ≠ 能解密数据；三道门由三种不同的策略把守：", "信任策略（角色上）、身份策略 / 秘密的资源策略、KMS 密钥策略（+ IAM 委托）"], "gray", size=9.8)
f.save("three-gates.svg")

# ---------------------------------------------------------------- 图 7-2 OIDC 时序
seq("oidc-seq.svg",
    [("gh", "GitHub Runner\nworkflow job", "gray"), ("idp", "GitHub OIDC\n令牌服务", "purple"),
     ("sts", "AWS STS", "navy"), ("sm", "Secrets Manager", "teal"), ("kms", "AWS KMS", "orange")],
    [("gh", "idp", "请求 JWT（需 id-token: write）"),
     ("idp", "gh", "JWT：iss / aud / sub / ref …", "ret"),
     ("gh", "sts", "AssumeRoleWithWebIdentity(JWT)"),
     ("note", "sts", "校验签名、aud、sub 与信任策略"),
     ("sts", "gh", "临时凭证（≤ 1 小时）", "ret"),
     ("gh", "sm", "GetSecretValue（角色会话）"),
     ("sm", "kms", "Decrypt(加密的数据密钥, 上下文)"),
     ("kms", "sm", "明文数据密钥", "ret"),
     ("sm", "gh", "秘密值（本实验只打印 VersionId）", "ret")],
    w=760, row=34, foot="GitHub 仓库里不存放任何长期访问密钥；凭证每次运行现取、自动过期")

# ---------------------------------------------------------------- 图 7-3 信封加密
f = Fig(760, 300)
f.text(24, 22, "写入（PutSecretValue）", size=11, weight=700, color=NAVY)
f.box(24, 36, 150, 56, "Secrets Manager", ["要保存秘密 v1"], "teal", title_size=11, size=9.4)
f.box(300, 36, 150, 56, "AWS KMS", ["GenerateDataKey", "（KMS 密钥不出 KMS）"], "orange", title_size=11, size=9.2)
f.arrow((174, 56), (300, 56), color=NAVY, label="密钥 ID + 加密上下文", dy=-6, label_size=9.2)
f.arrow((300, 78), (174, 78), color=ORANGE, label="明文数据密钥 + 加密的数据密钥", dy=16, label_size=9.2)
f.box(520, 30, 216, 70, "保存的只有：", ["AES-256 加密后的秘密值", "+ 加密后的数据密钥", "明文数据密钥用完即丢"], "gray", title_size=10.6, size=9.2, align="start")
f.text(24, 150, "读取（GetSecretValue）", size=11, weight=700, color=NAVY)
f.box(24, 164, 150, 56, "Secrets Manager", ["代调用者解密"], "teal", title_size=11, size=9.4)
f.box(300, 164, 150, 56, "AWS KMS", ["Decrypt", "检查调用者权限"], "orange", title_size=11, size=9.2)
f.arrow((174, 184), (300, 184), color=NAVY, label="加密的数据密钥 + 上下文", dy=-6, label_size=9.2)
f.arrow((300, 206), (174, 206), color=ORANGE, label="明文数据密钥（权限、上下文都对时）", dy=16, label_size=9.2)
f.box(520, 158, 216, 70, "加密上下文", ["SecretARN = 秘密 ARN", "SecretVersionId = 版本 ID", "与密文绑定，不一致就解不开"], "purple", title_size=10.6, size=9.2, align="start")
f.text(380, 262, "所以读秘密需要两种权限：secretsmanager:GetSecretValue（调用 API）+ kms:Decrypt（解开数据密钥）", size=10, color=NAVY, anchor="middle", weight=600)
f.text(380, 282, "使用 AWS 托管密钥 aws/secretsmanager 时，后者由它的密钥策略自动给予本账户（经 Secrets Manager 调用时）", size=9.6, color=MUTED, anchor="middle")
f.save("envelope.svg")

# ---------------------------------------------------------------- 图 7-4 KMS 授权两条腿
f = Fig(760, 240)
f.box(24, 30, 220, 80, "密钥策略（必需）", ["每把 KMS 密钥都有且必须有", "没有它允许，谁都用不了", "包括账户管理员"], "orange", title_size=11.5, size=9.4)
f.box(270, 30, 220, 80, "IAM 策略（可选的第二条腿）", ["只有密钥策略里", "“允许本账户 IAM 策略”", "时才生效"], "navy", title_size=11.5, size=9.4)
f.box(516, 30, 220, 80, "授权（Grant）", ["临时、可撤销的委托", "常被 AWS 服务代用", "（如 EBS、RDS）"], "purple", title_size=11.5, size=9.4)
f.box(24, 140, 712, 84, "判断 kms:Decrypt 能否成功", ["密钥策略直接允许该主体  →  可以",
                                                    "密钥策略允许账户（root）+ IAM 策略允许该主体  →  可以",
                                                    "密钥策略没有允许账户，只有 IAM 策略允许  →  不行（IAM 的 Allow 不生效）"], "gray", title_size=11, size=9.6, align="start")
f.save("kms-auth.svg")
print("A03-02 figures ok")
