"""A09-02（第 16 讲）figures."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE

# ---------------------------------------------------------------- 图 16-1 四道控制
f = Fig(760, 250)
ctl = [("① 审批", ["GitHub 受保护环境", "Required reviewers", "只允许 main 部署"], "purple", "作业等待审批"),
       ("② 身份", ["OIDC 令牌 → STS", "信任策略比对", "aud · sub · ref"], "navy", "AssumeRoleWithWebIdentity 被拒"),
       ("③ 权限", ["角色自己的策略", "状态桶 · .tflock", "业务资源"], "teal", "API AccessDenied"),
       ("④ 锁", ["S3 原生锁", "<key>.tflock", "同一状态单写入者"], "orange", "Error acquiring the state lock")]
for i, (t, ls, st, fail) in enumerate(ctl):
    x = 14 + i * 186
    f.box(x, 20, 168, 96, t, ls, st, title_size=12, size=9.2)
    if i < 3:
        f.arrow((x + 168, 68), (x + 186, 68))
    f.rect(x, 130, 168, 30, fill="#fbeceb", stroke="none", r=6)
    f.text(x + 84, 149, fail, size=9, color=RED, anchor="middle", weight=600)
f.text(380, 186, "每一道只回答自己的问题：", size=10.4, color=NAVY, anchor="middle", weight=700)
f.text(380, 206, "批准了 ≠ 信任匹配；能扮演角色 ≠ 有权限；有权限 ≠ 拿得到锁；拿到锁 ≠ 变更正确", size=10, color=INK, anchor="middle")
f.text(380, 228, "id-token: write 只允许“请求令牌”，本身不带任何 AWS 权限", size=9.6, color=MUTED, anchor="middle")
f.save("four-controls.svg")

# ---------------------------------------------------------------- 图 16-3 漂移：三方与三条路线
f = Fig(760, 270)
f.box(14, 20, 170, 64, "代码（期望）", ["enable_dns_hostnames = false"], "navy", title_size=11, size=9.2)
f.box(14, 104, 170, 64, "状态（上次所知）", ["地址 → ID / 属性"], "teal", title_size=11, size=9.2)
f.box(14, 188, 170, 64, "真实对象", ["enable_dns_hostnames = true"], "orange", title_size=11, size=9.2)
f.arrow((184, 52), (260, 92), color=NAVY, sw=1.3)
f.arrow((184, 220), (260, 120), color=ORANGE, sw=1.3)
f.box(260, 72, 200, 70, "terraform plan", ["~ enable_dns_hostnames", "  = true -> false（本讲实测）"], "white", title_size=11, size=9.2)
f.box(260, 170, 200, 64, "plan -refresh-only", ["只更新状态里的“所知”", "不改真实对象，也不改代码"], "white", title_size=10.5, size=9)
routes = [("恢复", "未经授权的改动：", "审查只恢复这一处的 plan，再 apply", GREEN),
          ("接受", "已批准的紧急变更：", "把新值写进代码，重新 plan 与审批", NAVY),
          ("暂停", "来源不明、风险不清：", "冻结写操作，保留证据，先调查", RED)]
for i, (t, l1, l2, col) in enumerate(routes):
    y = 30 + i * 74
    f.rect(500, y, 246, 62, fill="#ffffff", stroke=col, sw=1.4, r=8)
    f.text(512, y + 22, t, size=11.5, color=col, weight=800)
    f.text(512, y + 40, l1, size=9, color=INK)
    f.text(512, y + 54, l2, size=9, color=INK)
    f.arrow((460, 107), (500, y + 31), color=MUTED, sw=1.0)
f.save("drift-routes.svg")

# ---------------------------------------------------------------- 图 16-2 一条受保护的交付流水线
f = Fig(760, 220)
f.box(14, 20, 120, 60, "Pull request", ["改动 infra/"], "gray", title_size=11, size=9)
f.box(170, 20, 260, 60, "plan 作业", ["计划角色：只读 + 读状态 + 锁", "plan → show -json → 闸门（只看）"], "navy", title_size=11, size=9)
f.arrow((134, 50), (170, 50))
f.box(14, 120, 120, 60, "合入 main", ["push 事件"], "gray", title_size=11, size=9)
f.box(170, 120, 150, 60, "环境审批", ["production", "审批人 + 分支限制"], "purple", title_size=11, size=9)
f.box(356, 120, 390, 60, "apply 作业（同一状态排队执行）", ["应用角色（sub=…:environment:production，ref=main）", "plan -out → 闸门 --allow create,update,no-op → apply 这份计划"], "orange", title_size=10.5, size=9)
f.arrow((134, 150), (170, 150))
f.arrow((320, 150), (356, 150))
f.text(380, 206, "计划文件只在作业内部流转，不作为公开制品上传；应用角色与计划角色分开", size=9.6, color=NAVY, anchor="middle", weight=600)
f.save("pipeline-flow.svg")
print("A09-02 figures ok")
