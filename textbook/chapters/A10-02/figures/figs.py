"""A10-02（第 18 讲）figures."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE, LINE

# ---------------------------------------------------------------- 图 18-1 交付链与三个里程碑
f = Fig(760, 250)
st = [("申请", ["工单 / Git 请求"], "white"), ("创建", ["Organizations", "中出现账户 ID"], "navy"),
      ("纳管", ["OU 基线成功", "账户 ENROLLED"], "teal"), ("定制（可选）", ["AFT / CfCT / AFC", "LZA 配置"], "orange"),
      ("独立验收", ["日志真的送达", "身份真的可用"], "green")]
for i, (t, ls, s) in enumerate(st):
    x = 14 + i * 150
    f.box(x, 40, 132, 70, t, ls, s, title_size=11.5, size=9.4)
    if i < 4:
        f.arrow((x + 132, 75), (x + 150, 75))
for x0, x1, label, col in [(14, 296, "里程碑 ①  Account Created", NAVY), (314, 446, "②  Governed", TEAL),
                           (464, 746, "③  Customized & Accepted", GREEN)]:
    f.line(x0, 128, x1, 128, color=col, sw=2.4)
    f.text((x0 + x1) / 2, 146, label, size=10, color=col, anchor="middle", weight=700)
f.note(14, 170, 732, 66, ["每一个里程碑都要单独取证：账户存在 ≠ 已纳管；已纳管 ≠ 公司额外基线已生效；流水线成功 ≠ 业务验收通过。",
                          "并不是所有账户都经过 AFT：控制台 Account Factory、Organizations + 自动纳管、LZA 都是合法的开户路径。"],
       style="orange", size=9.6)
f.save("delivery-chain.svg")

# ---------------------------------------------------------------- 图 18-2 谁负责什么
f = Fig(760, 270)
f.box(14, 14, 732, 64, "治理平面：AWS Control Tower（着陆区）",
      ["OU 基线（AWSControlTowerBaseline）· 控制（预防 / 检测 / 主动）· 账户纳管与漂移 · 4.0 起各服务集成可选、可只用控制"],
      "solid-navy", title_size=12, size=9.6)
tools = [("Account Factory / AFC", ["控制台或 API 开户", "AFC：蓝图（CFN 或 TF）", "适合：少量、手工开户"], "teal"),
         ("AFT", ["Git 请求 + Terraform", "全局 / 账户两级定制", "适合：大量、GitOps 开户"], "orange"),
         ("CfCT", ["CloudFormation + SCP/RCP", "按生命周期事件推送", "适合：给 OU 推标准资源"], "purple"),
         ("LZA", ["配置文件 + CDK 流水线", "网络 / 安全 / 日志一体", "适合：受监管、复杂平台"], "navy")]
for i, (t, ls, s) in enumerate(tools):
    x = 14 + i * 186
    f.box(x, 100, 172, 92, t, ls, s, title_size=11.5, size=9.2)
    f.arrow((x + 86, 100), (x + 86, 78), color=MUTED, sw=1.0)
f.text(380, 222, "它们可以组合使用（例如 Control Tower + AFT + CfCT），不是四选一；每个工具都有自己的状态与证据。", size=10, color=NAVY, anchor="middle", weight=600)
f.text(380, 244, "LZA 推荐与 Control Tower 一起部署，也支持只基于 Organizations 的安装方式。", size=9.6, color=MUTED, anchor="middle")
f.save("tools-map.svg")

# ---------------------------------------------------------------- 图 18-3 AFT 的阶段与证据
f = Fig(760, 300)
stages = [("① 请求", ["aft-account-request", "仓库合入"], "white"), ("② 开户", ["Service Catalog", "或 Organizations"], "navy"),
          ("③ 框架", ["角色、标签、元数据", "provisioning-customizations"], "teal"), ("④ 全局定制", ["aft-global-", "customizations"], "orange"),
          ("⑤ 账户定制", ["aft-account-", "customizations/<模板名>"], "orange")]
for i, (t, ls, s) in enumerate(stages):
    x = 14 + i * 150
    f.box(x, 30, 136, 72, t, ls, s, title_size=11.5, size=8.8)
    if i < 4:
        f.arrow((x + 136, 66), (x + 150, 66))
ev = ["Git 提交、流水线执行", "账户 ID、目标 OU", "Step Functions 执行记录", "该账户的定制流水线", "模板名与流水线结果"]
for i, e in enumerate(ev):
    f.text(14 + i * 150 + 68, 122, e, size=8.8, color=MUTED, anchor="middle")
f.box(14, 146, 732, 44, None, ["⑥ 独立验收：在目标账户与接收端核对业务结果（日志样本、登录、标签）——流水线绿灯不能代替这一步"], "green", size=9.8)
f.box(14, 210, 356, 76, "重新执行定制：aft-invoke-customizations", ["按账户 / OU / 标签 / 全部选择，最多 5 个并发",
                                                           "plan_only: true → 只跑 terraform plan（1.22.0）",
                                                           "bypass_steps 跳过开户与引导阶段"], "white", title_size=10.5, size=9, align="start")
f.box(390, 210, 356, 76, "2026 年的变化（AFT 发行说明）", ["1.21.0：账户换 OU 时自动重跑定制（account_move）",
                                                       "1.24.0：可不经 Service Catalog 开户（需自动纳管）",
                                                       "1.20.0：Terraform 最低 1.6.1；1.18.0：AWS Provider ≥ 6"], "white", title_size=10.5, size=9, align="start")
f.save("aft-pipeline.svg")

# ---------------------------------------------------------------- 图 18-4 着陆区的账户结构
f = Fig(760, 270)
f.group(14, 14, 732, 244, "AWS Organizations（根）", "org", size=11)
f.box(30, 46, 200, 62, "管理账户", ["Organizations 与 Control Tower", "不能更换，不放工作负载"], "solid-navy", title_size=11, size=9)
f.group(250, 46, 230, 120, "Security OU（基础）", "ou", size=10)
f.box(262, 78, 100, 70, "Log Archive", ["集中日志", "长期留存"], "teal", title_size=10.5, size=8.8)
f.box(370, 78, 100, 70, "Audit", ["安全审计", "只读汇总"], "teal", title_size=10.5, size=8.8)
f.group(500, 46, 230, 120, "Sandbox / Workloads OU", "ou", size=10)
f.box(512, 78, 100, 70, "账户 A", ["已纳管"], "white", title_size=10.5, size=8.8)
f.box(620, 78, 100, 70, "账户 B", ["待验证"], "white", title_size=10.5, size=8.8, dash="5 3")
f.box(30, 124, 200, 52, "AFT 管理账户", ["独立 OU；承载 AFT 流水线"], "orange", title_size=10.5, size=9)
f.note(30, 190, 700, 56, ["4.0 起，Config、组织级 CloudTrail、Log Archive / Audit 账户等集成都可以单独选择；",
                          "在独立账户上启用 Control Tower 会新建组织，当前账户即成为管理账户（本书只看到向导，未创建）。"],
       style="orange", size=9.4)
f.save("lz-accounts.svg")
print("A10-02 figures ok")
