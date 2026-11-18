"""A09-01（第 15 讲）figures."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE

# ---------------------------------------------------------------- 图 15-1 从代码到变更
f = Fig(760, 250)
ins = [("配置", ["HCL + 模块 + 变量"], "navy"), ("状态", ["地址 → 对象 ID / 属性"], "teal"), ("真实对象", ["provider 刷新读取"], "gray")]
for i, (t, ls, st) in enumerate(ins):
    f.box(14, 14 + i * 64, 150, 52, t, ls, st, title_size=11, size=9)
    f.arrow((164, 40 + i * 64), (214, 104), color=MUTED, sw=1.2)
flow = [("plan", ["比较三方", "得出动作"], "orange"), ("审查", ["动作、原因", "范围、回退"], "purple"), ("保存的计划", ["-out=tfplan", "（敏感工件）"], "red"), ("apply", ["只执行", "被批准的那份"], "green")]
for i, (t, ls, st) in enumerate(flow):
    x = 214 + i * 136
    f.box(x, 72, 120, 64, t, ls, st, title_size=11.5, size=9)
    if i < 3:
        f.arrow((x + 120, 104), (x + 136, 104))
checks = [("fmt -check", "只证明排版"), ("validate", "只证明结构与参数有效"), ("plan", "只是基于当前信息的预测"), ("apply 成功", "还要独立验证业务")]
for i, (c, s) in enumerate(checks):
    x = 214 + i * 136
    f.text(x + 60, 160, c, size=10, color=NAVY, anchor="middle", weight=700, mono=True)
    f.text(x + 60, 177, s, size=9, color=RED, anchor="middle")
f.note(214, 192, 532, 50, ["validate 全绿，plan 里仍可能有一个“替换生产数据库”——", "审查的对象是动作和原因，不是退出码"], style="orange", size=9.6)
f.save("plan-pipeline.svg")

# ---------------------------------------------------------------- 图 15-2 计划里的动作
f = Fig(760, 220)
acts = [("+", "create", "新建对象", GREEN), ("~", "update", "原地修改", ORANGE), ("-/+", "replace", "先删后建（或先建后删）", RED),
        ("-", "delete", "销毁对象", RED), ("·", "no-op", "无变化（moved 只改地址）", MUTED), ("⌀", "forget", "不再管理，但不销毁", PURPLE)]
for i, (sym, name, desc, col) in enumerate(acts):
    x = 14 + (i % 3) * 248
    y = 14 + (i // 3) * 90
    f.rect(x, y, 236, 76, fill="#ffffff", stroke=col, sw=1.4, r=8)
    f.text(x + 36, y + 48, sym, size=22, color=col, anchor="middle", weight=800, mono=True)
    f.text(x + 72, y + 32, name, size=11.5, color=col, weight=800, mono=True)
    f.text(x + 72, y + 54, desc, size=9.6, color=INK)
f.text(380, 208, "replace 的原因看 action_reason：本章实测 triggers_replace 变化报告为 replace_because_cannot_update", size=9.6, color=NAVY, anchor="middle", weight=600)
f.save("plan-actions.svg")

# ---------------------------------------------------------------- 图 15-3 地址、状态与对象
f = Fig(760, 270)
f.box(14, 20, 220, 60, "旧地址", ["terraform_data.orders"], "gray", title_size=10.5, size=9.4)
f.box(14, 110, 220, 60, "新地址（加了 moved）", ["module.orders.terraform_data.release"], "teal", title_size=10.5, size=9.2)
f.box(14, 200, 220, 60, "新地址（忘了 moved）", ["module.order_svc.terraform_data.release"], "red", title_size=10.5, size=9.2)
f.box(300, 90, 170, 100, "状态中的对象", ["id = 87b15a20-…", "（本章实测）"], "navy", title_size=11, size=9.4)
f.arrow((234, 50), (300, 120), color=MUTED, sw=1.2, dash=True)
f.arrow((234, 140), (300, 140), "同一个对象", color=TEAL, sw=1.6, label_size=9)
f.arrow((234, 230), (530, 150), color=RED, sw=1.4)
f.text(330, 236, "找不到对应的状态：被当成新对象", size=9, color=RED, anchor="start")
f.box(530, 40, 216, 60, "plan：no-op", ["has moved to …", "对象 ID 不变"], "green", title_size=11, size=9)
f.box(530, 120, 216, 60, "plan：delete + create", ["旧对象销毁，新对象创建", "真实资源会被重建"], "red", title_size=11, size=9)
f.box(530, 200, 216, 60, "plan：forget（removed 块）", ["从状态中移除", "真实对象保留"], "purple", title_size=10.5, size=9)
f.arrow((470, 125), (530, 70), color=GREEN, sw=1.2)
f.save("address-mapping.svg")

# ---------------------------------------------------------------- 图 15-4 S3 远程状态
f = Fig(760, 240)
f.box(14, 30, 150, 70, "工程师 / CI", ["terraform plan / apply"], "white", title_size=11, size=9)
f.group(220, 14, 330, 210, "状态桶（单独引导创建）", "private", size=10.5)
f.box(240, 50, 290, 50, None, ["platform/dev/terraform.tfstate", "版本控制：写坏、误删可回滚"], "white", size=9.2)
f.box(240, 112, 290, 44, None, ["platform/dev/terraform.tfstate.tflock", "use_lockfile = true 时的锁对象"], "white", size=9.2)
f.box(240, 168, 290, 44, None, ["platform/prod/terraform.tfstate", "dev 的角色碰不到（模拟器实测）"], "gray", size=9.2)
f.arrow((164, 65), (240, 75), "读写状态", label_size=9)
f.arrow((164, 80), (240, 134), "加锁 / 解锁", label_size=9, dy=10)
f.note(570, 30, 176, 182, ["状态可能含明文机密：", "当作敏感数据保护", "", "S3 原生锁取代", "DynamoDB 锁（已弃用）", "", "锁卡住：先查持有者，", "不要 -lock=false"], style="orange", size=9.4, title="要点")
f.save("s3-backend.svg")
print("A09-01 figures ok")
