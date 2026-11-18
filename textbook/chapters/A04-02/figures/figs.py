"""A04-02（第 09 讲）figures."""
from figlib import Fig, seq, NAVY, TEAL, ORANGE, RED, GREEN, MUTED, INK, PURPLE


def nb(s: str) -> str:
    """SVG 会折叠连续空格：代码缩进改用不换行空格。"""
    return s.replace("  ", "  ")

# ---------------------------------------------------------------- 图 9-1 两条路径与四座桥
f = Fig(760, 362)
f.group(10, 8, 740, 132, "日志路径：有人来“问”，才有答案", "plain")
f.box(26, 52, 120, 72, "应用 / Agent", ["PutLogEvents", "写结构化 JSON"], "gray", title_size=11.5, size=9.8)
f.arrow((146, 88), (196, 88))
f.box(196, 52, 140, 72, "日志组", ["保留期 · 多个日志流", "按摄取量计费"], "navy", title_size=11.5, size=9.8)
f.arrow((336, 88), (392, 88))
f.box(392, 52, 172, 72, "Logs Insights", ["交互式查询 QL / PPL / SQL", "按扫描量计费"], "teal", title_size=11.5, size=9.8)
f.arrow((564, 88), (612, 88))
f.box(612, 52, 124, 72, "值班工程师", ["读结果、下结论"], "white", title_size=11.5, size=9.8)
f.text(736, 30, "交互式查询的结果不会自己变成事件", size=9.6, color=RED, anchor="end", weight=600)

f.group(10, 224, 740, 130, "事件路径：事情一发生，就“推”给订阅者", "plain")
f.box(26, 268, 120, 72, "发布者", ["应用 / CI / 脚本", "④ PutEvents"], "gray", title_size=11.5, size=9.8)
f.arrow((146, 304), (196, 304))
f.box(196, 268, 368, 72, "事件总线", ["默认总线：AWS 服务事件（告警状态变化、计划查询完成…）",
                                    "自定义总线：自己的业务事件（本章 a09-lab01）"], "orange", title_size=11.5, size=9.6)
f.arrow((564, 304), (612, 304), "匹配", label_size=9.2)
f.box(612, 268, 124, 72, "目标", ["SQS 值班队列", "重试 + 死信队列"], "green", title_size=11.5, size=9.8)

f.arrow((266, 124), (266, 268), color=PURPLE, sw=1.6)
f.pill(266, 182, "① 指标过滤器 → 告警", fill="#f1edf8", color=PURPLE, size=9.6, anchor="middle")
f.text(266, 200, "告警状态变化 → 默认总线", size=9, color=MUTED, anchor="middle")
f.arrow((478, 124), (478, 268), color=PURPLE, sw=1.6)
f.pill(478, 182, "② 计划查询  ③ 日志告警", fill="#f1edf8", color=PURPLE, size=9.6, anchor="middle")
f.text(478, 200, "按计划运行查询 → 默认总线", size=9, color=MUTED, anchor="middle")
f.save("two-paths.svg")

# ---------------------------------------------------------------- 图 9-2 一条日志事件的解剖
f = Fig(760, 300)
f.box(14, 14, 262, 176, "PutLogEvents 请求", [], "navy", title_size=11.2, valign="top")
code = ['logGroupName  /cloudops/a09/lab01', 'logStreamName sample-run-090412', 'logEvents: [',
        '  { timestamp: 1763370000000,', "    message: '{\"status\":500,", "      \"release\":\"v2\",…}' },", '  … 共 16 条，按时间递增 ]']
for i, s in enumerate(code):
    f.text(26, 58 + i * 18, nb(s), size=9.4, color=INK, mono=True)
f.arrow((276, 102), (322, 102), "写入", label_size=9.4)
f.group(322, 14, 150, 176, "日志组", "private", size=10.5)
f.box(334, 60, 126, 50, "日志流", ["sample-run-090412"], "white", title_size=10.5, size=9)
f.box(334, 124, 126, 50, "日志流", ["sample-run-091530"], "white", title_size=10.5, size=9)
f.arrow((472, 102), (512, 102), "查询", label_size=9.4)
f.box(512, 14, 234, 176, "Logs Insights 看到的字段", [], "teal", title_size=11.2, valign="top")
rows = [("@timestamp", "← 请求里的 timestamp（事件时间）"), ("@ingestionTime", "← 服务收到它的时间"),
        ("@logStream / @log", "← 流名 / 日志组标识"), ("@message", "← message 原文"),
        ("status, release…", "← JSON 字段自动发现")]
for i, (k, v) in enumerate(rows):
    f.text(524, 60 + i * 25, k, size=9.6, color=NAVY, weight=700, mono=True)
    f.text(524, 73 + i * 25, v, size=9.2, color=INK)
f.text(380, 214, "一批 PutLogEvents 的硬约束（违反时：整批失败，或部分事件被拒并在 rejectedLogEventsInfo 中报告）",
       size=9.8, color=NAVY, anchor="middle", weight=700)
chips = ["≤ 10 000 条", "≤ 1 MB（每条另计 26 字节）", "单条 ≤ 1 MB", "按时间递增", "跨度 ≤ 24 小时"]
x = 22
for c in chips:
    x += f.pill(x, 242, c, fill="#e9eff5", color=NAVY, size=9.4) + 8
chips2 = [("早于 14 天或早于保留期 → 拒收（tooOld）", "#fbeceb", RED), ("晚于 2 小时后 → 拒收（tooNew）", "#fbeceb", RED),
          ("序列号已废弃，可并行写", "#eaf5ee", GREEN)]
x = 22
for c, bg, col in chips2:
    x += f.pill(x, 274, c, fill=bg, color=col, size=9.4) + 8
f.save("log-anatomy.svg")

# ---------------------------------------------------------------- 图 9-3 管道：16 → 6 → 1，以及分母
f = Fig(760, 300)
stages = [("16 条事件", "全部日志", "gray"), ("6 条", "status ≥ 500", "orange"), ("1 行", "canary · v2 · /checkout · 6", "teal"),
          ("排序后", "最严重的分组在第一行", "navy")]
ops = ["filter status >= 500", "stats count(*) by\nphase, release, route", "sort errors desc"]
xs = [14, 206, 398, 590]
for i, (t, s, st) in enumerate(stages):
    f.box(xs[i], 20, 156, 62, t, [s], st, title_size=12.5, size=9.4)
    if i < 3:
        f.arrow((xs[i] + 156, 51), (xs[i + 1], 51), color=NAVY)
        for j, part in enumerate(ops[i].split("\n")):
            f.text((xs[i] + 156 + xs[i + 1]) / 2, 100 + j * 13, part, size=9, color=NAVY, anchor="middle", mono=True)
f.text(380, 146, "同一个问题“错误率是多少”，三种写法三个答案——差别全在分母", size=11, color=NAVY, anchor="middle", weight=700)
f.box(14, 162, 236, 124, "✗ 先 filter 再算", ["`filter status >= 500`", "`| stats count(*) as requests,`", nb("`    sum(if(…)) as errors`"), "",
                                             "requests = 6 → “100%”"], "red", title_size=11, size=9.2, align="start")
f.box(262, 162, 236, 124, "✗ 用全部请求当分母", ["`stats 100 * sum(if(…))`", nb("`    / count(*) as pct`"), "（没有 by phase）", "",
                                               "6 ÷ 16 = 37.5%"], "red", title_size=11, size=9.2, align="start")
f.box(510, 162, 236, 124, "✓ 同一分组内算分子与分母", ["`stats count(*) as requests,`", nb("`  sum(if(status >= 500, 1, 0))`"), nb("`  as errors … by phase, release`"), "",
                                                   "canary：6 ÷ 8 = 75%"], "green", title_size=11, size=9.2, align="start")
f.save("pipeline.svg")

# ---------------------------------------------------------------- 图 9-4 事件模式如何命中
f = Fig(760, 232)
f.box(14, 14, 300, 150, "事件模式（规则）", [], "orange", title_size=11.2, valign="top")
pat = ['{', '  "source": ["cloudops.lab"],', '  "detail-type": ["DeploymentAnomaly"],', '  "detail": {', '    "severity": ["high"]', '  }', '}']
for i, s in enumerate(pat):
    f.text(28, 54 + i * 15.5, nb(s), size=9.6, mono=True, color=INK)
f.box(446, 14, 300, 150, "事件（PutEvents 之后的信封）", [], "navy", title_size=11.2, valign="top")
ev = ['{', '  "source": "cloudops.lab",', '  "detail-type": "DeploymentAnomaly",', '  "detail": {', '    "service": "checkout",',
      '    "severity": "high", "errorRate": 75', '  }  … id / time / region / account }']
for i, s in enumerate(ev):
    f.text(460, 54 + i * 15.5, nb(s), size=9.6, mono=True, color=INK)
for (y1, y2), cx in (((65.5, 65.5), 352), ((81, 81), 380), ((112.5, 127), 408)):
    f.arrow((314, y1), (446, y2), color=GREEN, sw=1.3, head="both")
    f.circle(cx, y1 + (y2 - y1) * (cx - 314) / 132, 8, fill="#ffffff", stroke="none")
    f.check(cx, y1 + (y2 - y1) * (cx - 314) / 132 + 4, ok=True, size=11)
f.text(380, 186, "模式里列出的字段全部满足（AND）→ 命中；事件里多出来的字段不影响匹配", size=10.4, color=NAVY, anchor="middle", weight=700)
rules = [("字段之间 AND · 数组之内 OR · 事件数组求交集", "teal"), ("精确匹配：区分大小写，也区分类型", "red"),
         ("缺失字段只被 exists:false 命中", "red")]
for i, (s, st) in enumerate(rules):
    fill, col = {"teal": ("#e6f3f3", "#12676b"), "red": ("#fbeceb", "#8e2f2c")}[st]
    f.rect(14 + i * 248, 198, 236, 28, fill=fill, stroke="none", r=6)
    f.text(14 + i * 248 + 118, 216.5, s, size=9.4, color=col, anchor="middle", weight=600)
f.save("pattern-match.svg")

# ---------------------------------------------------------------- 图 9-5 投递链：每一步的证据
seq("delivery-chain.svg",
    [("pub", "发布者\nsend-events.sh", "gray"), ("bus", "自定义总线\n+ 规则", "orange"), ("sqs", "值班队列\nSQS", "green"),
     ("dlq", "死信队列\nDLQ", "red"), ("con", "值班消费者\nreceive.sh", "navy")],
    [("pub", "bus", "PutEvents（3 条）"),
     ("bus", "pub", "3 个 EventId：只证明“总线收下了”", "ret"),
     ("self", "bus", "逐条比对模式：只有 1 条命中（MatchedEvents）"),
     ("bus", "sqs", "SendMessage（输入转换后的 JSON）→ Invocations"),
     ("note", "bus:dlq", "前提：队列策略 aws:SourceArn = 规则 ARN；若用 KMS 还要密钥策略"),
     ("bus", "dlq", "无权限 / 目标不存在：不重试，直接进 DLQ", "err"),
     ("note", "bus:dlq", "可重试错误：按重试策略（本章 1 小时 / 10 次）退避重试，耗尽再进 DLQ"),
     ("con", "sqs", "ReceiveMessage（长轮询 10 秒）"),
     ("sqs", "con", "消息 + ReceiptHandle；30 秒内对其他消费者不可见", "ret"),
     ("con", "sqs", "DeleteMessage = 确认消费；不删则超时后重新出现")],
    w=760, row=33)
print("A04-02 figures ok")
