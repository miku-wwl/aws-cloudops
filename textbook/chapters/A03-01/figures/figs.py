"""A03-01（第 06 讲）figures."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE

# ---------------------------------------------------------------- 图 6-1 两次授权
f = Fig(760, 250)
f.box(16, 70, 140, 70, "操作者", ["IAM 用户 ci-operator", "（长期凭证）"], "gray", title_size=11.5, size=9.4)
f.box(220, 60, 170, 90, "① sts:AssumeRole", ["检查角色的信任策略：", "Principal 是否包含调用者", "（同时看调用者自身权限）"], "navy", title_size=11.5, size=9.2)
f.box(450, 70, 130, 70, "角色会话", ["assumed-role/…", "临时凭证 ≤ 1 小时"], "teal", title_size=11.5, size=9.2)
f.box(620, 60, 126, 90, "② s3:GetObject", ["检查角色权限策略、", "桶策略、边界、", "会话策略、SCP…"], "orange", title_size=11.5, size=9.2)
f.arrow((156, 105), (220, 105), color=NAVY, sw=1.6)
f.arrow((390, 105), (450, 105), color=NAVY, sw=1.6, label="临时凭证", dy=-6, label_size=9.4)
f.arrow((580, 105), (620, 105), color=NAVY, sw=1.6)
f.text(305, 182, "信任策略回答：谁能变成这个角色？", size=10.4, color=NAVY, anchor="middle", weight=700)
f.text(683, 182, "权限策略回答：变成之后能做什么？", size=10.4, color=ORANGE, anchor="middle", weight=700)
f.text(380, 222, "两次判定彼此独立：AssumeRole 成功，只证明拿到了身份，不证明有权读取某个对象", size=10, color=MUTED, anchor="middle")
f.save("two-decisions.svg")

# ---------------------------------------------------------------- 图 6-2 评估流程（单账户）
f = Fig(760, 470)
steps = [
    ("① 任何适用策略里有 Deny 吗？", "身份 / 资源 / 边界 / 会话 / SCP / RCP", RED, "是 → 显式拒绝 explicitDeny"),
    ("② SCP、RCP 允许吗？（若存在）", "组织策略只设上限，不授予权限", NAVY, "否 → 隐式拒绝"),
    ("③ 资源策略直接授予调用者？", "同账户：授予 IAM 用户 / 角色会话 ARN", TEAL, "是 → 允许（不受④⑤⑥的隐式拒绝影响）"),
    ("④ 身份策略允许吗？", "用户 / 组 / 角色上的策略", NAVY, "否（且资源策略也没允许）→ 隐式拒绝"),
    ("⑤ 权限边界允许吗？（若存在）", "边界只设上限", PURPLE, "否 → 隐式拒绝"),
    ("⑥ 会话策略允许吗？（若存在）", "AssumeRole 时传入的 --policy", PURPLE, "否 → 隐式拒绝"),
]
y = 16
for i, (q, sub, col, out) in enumerate(steps):
    st = {RED: "red", NAVY: "navy", TEAL: "teal", PURPLE: "purple"}[col]
    f.box(24, y, 330, 56, q, [sub], st, title_size=11, size=9.2)
    f.arrow((354, y + 28), (420, y + 28), color=col, sw=1.4)
    f.text(428, y + 32, out, size=10, color=col if col != NAVY else INK, weight=600)
    if i < len(steps) - 1:
        f.arrow((189, y + 56), (189, y + 72), color=MUTED, sw=1.4)
    y += 72
f.box(24, y, 330, 34, None, ["全部通过 → 允许（allowed）"], "solid-teal", size=10.6)
f.text(560, y + 22, "默认：一切请求都被隐式拒绝", size=10, color=MUTED, anchor="middle")
f.save("eval-flow.svg")

# ---------------------------------------------------------------- 图 6-3 交集与上限
f = Fig(760, 260)
f.circle(230, 128, 92, fill="#e6f3f3", stroke=TEAL, sw=1.6)
f.circle(340, 128, 92, fill="#f1edf8", stroke=PURPLE, sw=1.6)
f.text(180, 128, "身份策略", size=11, color="#12676b", anchor="middle", weight=700)
f.text(180, 146, "s3:* on a06-lab/*", size=9.4, color=INK, anchor="middle")
f.text(392, 128, "权限边界", size=11, color="#4f3a86", anchor="middle", weight=700)
f.text(392, 146, "GetObject on logs/*", size=9.4, color=INK, anchor="middle")
f.text(285, 120, "有效", size=10.6, color=NAVY, anchor="middle", weight=800)
f.text(285, 138, "权限", size=10.6, color=NAVY, anchor="middle", weight=800)
f.box(470, 30, 276, 92, "读 logs/health.txt", ["两者都允许 → allowed", "（AWS 模拟器实测：allowed）"], "green", title_size=11, size=9.6)
f.box(470, 140, 276, 92, "读 reports/summary.csv", ["身份策略允许，边界不允许", "→ implicitDeny（实测一致）"], "red", title_size=11, size=9.6)
f.text(285, 246, "边界、SCP、会话策略都是“上限”：只能收窄，不能授予", size=10, color=MUTED, anchor="middle")
f.save("boundary-intersection.svg")
print("A03-01 figures ok")
