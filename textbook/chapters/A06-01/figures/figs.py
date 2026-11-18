"""A06-01（第 11 讲）figures."""
from figlib import Fig, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE


def nb(s: str) -> str:
    return s.replace("  ", "  ")


# ---------------------------------------------------------------- 图 11-1 一次变更，三份证据
f = Fig(760, 300)
f.box(14, 112, 136, 72, "一次 API 调用", ["PutBucketTagging", "（某个身份、某个时刻）"], "navy", title_size=11.5, size=9.4)
items = [(38, "行为证据 · CloudTrail", ["谁、何时、调用了什么、成功与否", "事件历史：管理事件、90 天、单区域"], "orange"),
         (118, "现状证据 · S3 API", ["此刻的标签集是什么", "get-bucket-tagging：立即反映"], "teal"),
         (198, "评价证据 · AWS Config", ["配置项（CI）→ 规则评估 → 合规结果", "异步：几分钟后才有结论"], "purple")]
for y, t, lines, st in items:
    f.box(220, y, 300, 66, t, lines, st, title_size=11, size=9.2)
    f.arrow((150, 148), (220, y + 33), color=MUTED, sw=1.3)
f.box(568, 38, 178, 66, None, ["能证明：调用发生过、结果码", "不能证明：此刻的状态"], "white", size=9, align="start")
f.box(568, 118, 178, 66, None, ["能证明：当前事实", "不能证明：是谁、何时改的"], "white", size=9, align="start")
f.box(568, 198, 178, 66, None, ["能证明：某次评估时不合规", "不能证明：操作者是谁"], "white", size=9, align="start")
for y in (71, 151, 231):
    f.arrow((520, y), (568, y), color=MUTED, sw=1.2)
f.text(380, 22, "调查顺序：先锁定时间窗和资源 → 行为 → 现状 → 评价；三者不是一条自动调用链", size=10, color=NAVY, anchor="middle", weight=700)
f.text(380, 290, "预防（SCP / RCP / IAM）作用在“调用之前”；以上三份证据都发生在“调用之后”", size=9.6, color=RED, anchor="middle", weight=600)
f.save("three-evidence.svg")

# ---------------------------------------------------------------- 图 11-2 一条事件的解剖（真实事件，已脱敏）
f = Fig(760, 300)
f.box(14, 14, 380, 272, "CloudTrail 事件（本书实验 9-2 的真实调用，已脱敏）", [], "gray", title_size=10.6, valign="top")
lines = ['{ "eventTime": "2026-11-17T09:31:31Z",', '  "eventSource": "events.amazonaws.com",', '  "eventName": "TestEventPattern",',
         '  "awsRegion": "us-east-1",', '  "readOnly": true, "eventCategory": "Management",', '  "userIdentity": { "type": "IAMUser",',
         '     "arn": "arn:aws:iam::111122223333:user/<user>" },', '  "sourceIPAddress": "203.0.113.x",',
         '  "requestParameters": { "eventPattern": …, "event": … },', '  "errorCode": null,', '  "eventID": "27f32a68-…" }']
for i, s in enumerate(lines):
    f.text(26, 58 + i * 20, nb(s), size=9.2, mono=True, color=INK)
notes = [(58, "时间一律是 UTC（本机在 UTC+13）", NAVY), (98, "服务 + API：先确认“是不是要找的那类调用”", NAVY),
         (138, "只读调用也会记录；用 ReadOnly=false 只看写操作", TEAL), (178, "AssumedRole 时还要看 sessionIssuer 与会话名", ORANGE),
         (218, "敏感参数可能被隐藏：isRedacted / HIDDEN_DUE_…", RED), (258, "失败的调用也有事件：errorCode ≠ null 不改变状态", RED)]
for y, s, col in notes:
    f.arrow((394, y - 4), (418, y - 4), color=col, sw=1.2)
    f.text(424, y, s, size=9.4, color=col, weight=600)
f.save("event-anatomy.svg")

# ---------------------------------------------------------------- 图 11-3 Config 的流水线
f = Fig(760, 250)
stages = [("配置记录器", ["记录哪些资源类型", "连续 / 每日"], "navy"), ("配置项 CI", ["资源某一时刻的", "完整配置快照"], "teal"),
          ("规则评估", ["配置变化触发", "或按周期触发"], "purple"), ("合规结果", ["`COMPLIANT`", "`NON_COMPLIANT`"], "orange")]
for i, (t, ls, st) in enumerate(stages):
    x = 14 + i * 186
    f.box(x, 24, 160, 70, t, ls, st, title_size=11.5, size=9.2)
    if i < 3:
        f.arrow((x + 160, 59), (x + 186, 59))
f.box(200, 124, 160, 50, "投递通道", ["配置历史 → S3 桶"], "gray", title_size=10.5, size=9)
f.arrow((280, 94), (280, 124), color=MUTED, sw=1.2)
costs = [(94, "0.003 美元 / CI（连续）", "0.012 美元 / CI（每日）"), (466, "0.001 美元 / 次评估", "（每月前 10 万次）")]
for x, a, b in costs:
    f.text(x, 118, a, size=9.2, color=GREEN, anchor="middle", weight=600)
    f.text(x, 132, b, size=9, color=MUTED, anchor="middle")
f.note(390, 146, 356, 92, ["一个账户的一个区域只能有一个“客户托管”记录器", "（另有 AWS 服务创建的服务关联记录器）", "记录 S3 类型 = 记录本区域所有桶，不只是实验桶",
                          "没有评估结果 ≠ 合规；规则范围外的资源不会被评估"], style="orange", size=9.2, title="易错点")
f.save("config-pipeline.svg")

# ---------------------------------------------------------------- 图 11-4 三种标签 API 的语义
f = Fig(760, 238)
before = ["Project", "Environment", "Owner", "Chapter"]
cases = [("PutBucketTagging", "请求：{Project, CostCenter}", ["Project", "CostCenter"], "整体替换：没写进去的全被删", RED),
         ("TagResource", "请求：{CostCenter}", before + ["CostCenter"], "合并：只增加或覆盖请求里的键", GREEN),
         ("UntagResource", "请求：[Owner]", ["Project", "Environment", "Chapter"], "按键删除：可用 aws:TagKeys 拦住", ORANGE)]
for i, (api, req, after, verdict, col) in enumerate(cases):
    x = 14 + i * 250
    f.text(x + 115, 20, api, size=11.5, color=NAVY, anchor="middle", weight=800)
    f.text(x + 115, 38, req, size=9.2, color=MUTED, anchor="middle")
    for j, k in enumerate(after):
        lost = k == "Owner" and k not in after
        f.rect(x + 20, 52 + j * 26, 190, 22, fill="#eaf5ee" if k != "CostCenter" else "#e6f3f3", stroke="none", r=5)
        f.text(x + 115, 67 + j * 26, k, size=9.4, color=INK, anchor="middle")
    if "Owner" not in after:
        f.text(x + 115, 67 + len(after) * 26, "Owner 不见了", size=9.6, color=RED, anchor="middle", weight=700)
    f.text(x + 115, 222, verdict, size=9.4, color=col, anchor="middle", weight=700)
f.save("tag-apis.svg")

# ---------------------------------------------------------------- 图 11-5 控制在时间轴上的位置
f = Fig(760, 220)
axis = [("提交模板", 85), ("授权", 245), ("资源变化", 395), ("记录与评估", 535), ("修复", 680)]
f.line(30, 110, 740, 110, color=NAVY, sw=2)
for t, x in axis:
    f.circle(x, 110, 6, fill=NAVY, stroke="none")
    f.text(x, 134, t, size=9.8, color=NAVY, anchor="middle", weight=700)
ctrls = [(85, "主动式（Proactive）", ["CloudFormation Hooks", "只管走 CFN 的变更"], "teal"),
         (245, "预防式（Preventive）", ["SCP / RCP / IAM 拒绝", "API 直接失败"], "navy"),
         (535, "检测式（Detective）", ["AWS Config 规则", "只报告，不阻止"], "purple"),
         (680, "纠正式（Corrective）", ["Terraform / 自动修复", "回到代码里的基线"], "orange")]
for x, t, ls, st in ctrls:
    f.box(x - 68, 14, 136, 70, t, ls, st, title_size=10, size=8.8)
    f.arrow((x, 84), (x, 104), color=MUTED, sw=1.2)
f.box(315, 150, 160, 52, "CloudTrail", ["记录每一步的调用"], "gray", title_size=10.5, size=9)
f.arrow((395, 150), (395, 116), color=MUTED, sw=1.2, dash=True)
f.text(560, 176, "不在组织中的独立账户没有 SCP/RCP：", size=9.2, color=RED, anchor="start", weight=600)
f.text(560, 192, "护栏只能写在 IAM 策略或权限边界里", size=9.2, color=RED, anchor="start", weight=600)
f.save("control-timeline.svg")
print("A06-01 figures ok")
