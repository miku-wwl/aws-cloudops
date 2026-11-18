# 进度与约定（逐讲完成，完成一讲再进入下一讲）

## 讲次编号（图号前缀 = 讲次）

| 讲 | 源 PDF | 目录 | 状态 |
|---|---|---|---|
| 01 | A00-01 Landing Zone | chapters/A00-01 | ✅ 完成（22 页，6 张实拍，5 图，Terraform test 5/5） |
| 02 | A01-01 Well-Architected 与可靠性 | chapters/A01-01 | ✅ 完成（17 页，4 张实拍，5 图，unittest 8/8，terraform test 6/6，真实 plan） |
| 03 | A02-01 VPC 路由与 NACL | chapters/A02-01 | ✅ 完成（15 页，6 张实拍，6 图，unittest 9/9，terraform test 6/6，真实 plan） |
| 04 | A02-02 Security Group | chapters/A02-02 | ✅ 完成（12 页，5 张实拍，4 图，unittest 5/5，terraform test 6/6，真实 plan；sgaudit 已对真实账户运行） |
| 05 | A02-03 DNS 与 Endpoint | chapters/A02-03 | ✅ 完成（12 页，3 张实拍，4 图，layers 探针对真实端点实测，terraform test 4/4，真实 plan） |
| 06 | A03-01 IAM 评估与 STS | chapters/A03-01 | ✅ 完成（12 页，2 张实拍，3 图，iameval 与 AWS 模拟器 12 判定 0 差异，Access Analyzer 实测，terraform test 6/6，真实 plan） |
| 07 | A03-02 Federation / KMS / Secrets | chapters/A03-02 | ✅ 完成（13 页，3 张实拍，5 图，Access Analyzer 实测、真实密钥策略、信封加密演示，terraform test 7/7，真实 plan） |
| 08 | A04-01 CloudWatch Metrics & Alarms | chapters/A04-01 | ✅ 完成（12 页，3 张实拍，4 图，alarmsim 复现官方判定表 40/40，terraform test 5/5，真实 plan） |
| 09 | A04-02 Logs Insights & EventBridge | chapters/A04-02 | ✅ 完成（17 页，4 张实拍，5 图，本地引擎 unittest 14/14，20 个模式用例与真实 TestEventPattern 0 差异，terraform test 8/8，真实 plan 15/18；⚠ 4 张实拍待补：控制台会话过期） |
| 10 | A05-01 SSM 运维与只读自动化 | chapters/A05-01 | ✅ 完成（16 页，4 张实拍，5 图，ssmdiag 12 场景 unittest 8/8，操作者策略 10 判定与 IAM 模拟器 0 差异，terraform test 6/6，真实 plan 4/15，after-destroy 只读实跑） |
| 11 | A06-01 CloudTrail & Config | chapters/A06-01 | ✅ 完成（14 页，3 张实拍，5 图，事件历史真实查询+脱敏，护栏 6 判定与 IAM 模拟器 0 差异（IAM/SCP 两种校验无发现），terraform test 5/5，真实 plan 4/11，preflight 只读实跑） |
| 12 | A06-02 Security Hub / GuardDuty / 数据保护 | chapters/A06-02 | ✅ 完成（11 页，2 张实拍（合成），4 图，两道门模型 unittest 5/5，posture 只读实跑，TLS 桶策略模拟器实测 + KMS 模拟器局限实测，terraform test 4/4，真实 plan 7/9） |
| 13 | A07-01 Backup / Restore / DR | chapters/A07-01 | ✅ 完成（11 页，2 张实拍，4 图，recovery/canon unittest 6/6，preflight 只读实跑，terraform test 5/5，真实 plan 8） |
| 14 | A08-01 Incident Response & RCA | chapters/A08-01 | ✅ 完成（10 页，1 张实拍，4 图，ir.py 鉴别诊断/时间窗 unittest 4/4，terraform test 4/4，真实 plan 9，事件计数只读实测） |
| 15 | A09-01 Terraform Plan / State / 模块 | chapters/A09-01 | ✅ 完成（8 页，4 图，本机真实运行六阶段（moved/replace/forget/敏感值落盘），inspect_plan unittest 5/5，状态访问策略模拟器 8/8，terraform test 2/2，真实 plan 7） |
| 16 | A09-02 Remote State / OIDC / Drift | chapters/A09-02 | ✅ 完成（8 页，1 张实拍，3 图，四道控制推理模型 unittest 3/3，默认 VPC 只读 import-plan 漂移实测（1 import / 1 change），配置生成局限实测，信任策略 Access Analyzer 实测，工作流 YAML 校验） |
| 17 | A10-01 TGW / VPN / 企业 DNS | chapters/A10-01 | ✅ 完成（11 页，1 张实拍，4 图，hybrid 往返模型 12 场景 unittest 8/8，terraform test 6/6，真实只读 plan 0/23，Resolver/TGW 只读盘点） |
| 18 | A10-02 Control Tower / AFT / LZA | chapters/A10-02 | ✅ 完成（11 页，2 张实拍，4 图，delivery 判定器 10 案例 unittest 6/6，AFT 请求离线 terraform test 6/6，治理现状只读盘点） |
| 19 | FIN-01 FinOps 成本回收 | chapters/FIN-01 | ✅ 完成（10 页，2 张实拍，4 图，audit 6 案例 unittest 6/6，真实单价估算，3 区域只读盘点（发现孤立日志组），terraform test 4/4，真实只读 plan） |

## 每讲流程

1. 提取原 PDF 文字（pypdf，UTF-8）→ 通读，列出技术错误与过时点。
2. 用 AWS 官方文档 / Terraform Registry 核对关键事实（版本、字段、限制、默认值）。
3. 控制台只读截图：注入脱敏 + zoom 脚本 → 截图 → `tools/shot.py` 裁剪。不点任何创建/启用按钮。
4. 实验工程：Terraform（`fmt`/`validate`/`test` + mock provider）、只读脚本，真实执行并把输出写进教材。
5. `figures/figs.py` 画机制图 / 架构图。
6. 写 `chapter.md`：章首页 → 机制 → 决策 → 实操 → 验收 → 故障 → 练习与答案 → 要点 → 参考资料。
7. `python tools/build.py <id>` → 看联系表 → `tools/pages.py` 两页一图逐页审阅 → 修正 → 重建。

## 环境备忘

- AWS：只读。账户 ID 在截图/输出中替换为 111122223333，别名替换为 cloudops-lab。
- Terraform：使用私有 CLI 配置 `TF_CLI_CONFIG_FILE=<scratchpad>/terraformrc`（用户全局配置指向不存在的 D:/tf-plugin-cache）。
- 浏览器窗口若被最小化，截图会超时：用 `tools/edge_window.ps1 -Mode bottom` 恢复并置于底层（不抢焦点）。
- 控制台 zoom 后 `zoom` 动作的区域坐标以约 1400 宽为界；整屏截图用 `screenshot scale=1`。
- 离开填过表单的控制台页面前先执行 JS 去掉 beforeunload，避免原生对话框卡住浏览器。
- Git Bash 调 AWS CLI 传 `/aws/...` 之类参数时设 `MSYS_NO_PATHCONV=1`。
- Lambda 控制台 2026 起称 “Event Function”；运行时选 python3.14；账户 Lambda 并发配额为 10。
- 脱敏脚本必须用 `tools/console_prep.js`（遍历 shadow DOM 与同源 iframe，每 300ms 重扫）；旧版只扫主文档会漏掉 Owner ID。
- 默认 VPC（us-east-1）：vpc-0a891659a4b172ecd、主路由表 rtb-07cdae98c2171a114、默认 NACL acl-0a6ad3dfff164f944、IGW igw-006c0b467e462eb9a。
- 版式：例题/实验/故障卡标题由 build.py 生成真实 div.box-title；不要再用 .opener.newpage（易产生空白页）。
- terraform test 断言计算属性（资源 ID）时，在 mock_provider 中加 `override_during = plan` 并为相应资源写 mock_resource 默认值。
- PowerShell 工具会话失效时，改用 Bash 调 powershell.exe；.ps1 文件统一 UTF-8 BOM（PS 5.1 兼容）。
- IAM 控制台策略编辑器（Ace）程序化输入不会触发校验面板，改用 accessanalyzer validate-policy 的真实输出。
- CloudTrail 控制台横幅：CloudTrail Lake 自 2026-05-31 起不再向新客户开放（第 11 讲要写进去）。
- 2026 新事实：IAM 共享 OIDC 提供商控制（GitHub 信任必须评估 sub/job_workflow_ref）；GitHub 不可变 sub（2026-07-15 后新仓库 repo:owner@id/repo@id）；本仓库创建于 2026-10-31；configure-aws-credentials 最新 v6.3.0；Terraform 只写参数 secret_string_wo（TF≥1.11）。
- 打包时排除各 labs 下的 .terraform/、.terraform.lock.hcl、build/ 目录。
- CloudWatch 2026：告警数据源 Metrics/Logs/Alarms，类型 Classic/PromQL，EvaluationWindow 滑动/挂钟窗口。
- 所有讲完成后需用最新 tools 统一重建一遍（01、02 讲是在 box-title 改动前构建的）。
- 2026-11-18 Edge 中 AWS 控制台会话过期（新标签跳转登录页）：不能代为登录。待补截图清单见下方“待补截图”。MCP 标签冻结（innerWidth=0、CDP 超时）时：resize_window 或新建标签。
- 2026 新事实（第 19 讲）：t4g.nano 0.0042/h、gp3 0.08/GB·月、快照 0.05/GB·月、公网 IPv4 0.005/h（闲置同价）、日志写入 0.50/GB、存储 0.03/GB·月；预算无动作免费、前两个带动作的免费之后 0.10/天；成本分摊标签回填最多 12 个月（管理账户，每 24 小时一次）；2026-09-30 后新的预算邮件收件人需验证；本账户 15 个成本分摊标签键均 Inactive；us-west-2 有一个 2025-07 的孤立 Lambda 日志组（永不过期，449 字节，函数已不存在）；HCL 中 `$${` 是转义，标签过滤值改用 format()。
- 2026 新事实（第 18 讲）：Control Tower 着陆区 4.0（2025-11-17）各服务集成可选、可只用控制；自动纳管 3.3 起；AFT 1.20.0 Terraform≥1.6.1、1.21.0 换 OU 自动重跑定制（account_move）、1.22.0 plan_only、1.23.0 CodeBuild AL2023、1.24.0 可经 Organizations 开户（需自动纳管）并在定制前检查 OU 基线；aft_enable_vpc/aft_vpc_endpoints 默认 true；NAT 0.045/h、接口端点 0.01/h·AZ；LZA 示例约 430.22 美元/月；本账户不属于任何组织、无着陆区，list-enabled-baselines 报无法扮演 AWSControlTowerAdmin；CT 设置向导第 2 步会新建组织并使当前账户成为不可更换的管理账户（未点击）。
- 2026 新事实（第 17 讲）：TGW 选路顺序（最长前缀；同前缀 静态>系统(1:1 NAT)>前缀列表>VPC>DX>Connect>VPN over DX>VPN>VPN Concentrator>Client VPN>peering）；TGW 附件 0.05/h、数据 0.02/GB；VPN 0.05/h，5 Gbps 大带宽隧道（2025-11，仅 TGW/Cloud WAN）0.60/h，2026-05 可改带宽档；VPN Concentrator（2025-11）1.95/h + 0.01/h·站点；Route 53 Resolver 2025-11 改称 VPC Resolver，Global Resolver 2026-03 GA；Resolver 网卡 0.125/h、查询 0.40/百万；本账户 0 TGW/VPN/CGW/端点/托管区，只有 autodefined Internet Resolver 规则；控制台建 TGW 默认勾选默认表关联与传播；terraform test 断言不同实例的计算 ID 用 override_resource（target 可带实例键）。
- 2026 新事实（第 16 讲）：actions/checkout 最新 v7（v7.0.1）；hashicorp/setup-terraform v4（v4.0.1，需 Node 24，terraform_wrapper 默认 true——把 show -json 重定向到文件时关掉）；Access Analyzer 对 sub 不含分支的 GitHub 信任给 WARNING SPECIFIC_GITHUB_REPO_AND_BRANCH_RECOMMENDED，加 token.actions.githubusercontent.com:ref 后消失（PR 角色无法消除，故只读）；-generate-config-out 生成的 aws_vpc 含 ipv6_netmask_length = 0，plan 报 Missing required argument。
- 2026 新事实（第 15 讲）：Terraform 最新 1.17.2（2026-11-11，策略即代码 GA、-minimal-refresh）；本机 1.15.5；triggers_replace 的替换原因实测为 replace_because_cannot_update；sensitive 值在 plan JSON 中为明文；S3 后端 use_lockfile 原生锁，DynamoDB 锁弃用；Windows 下 python3 可能是商店占位符——脚本统一用 'PY=python3; $PY -c import sys || PY=python'。
- 2026 新事实（第 14 讲）：CloudWatch investigations 2025-06-24 GA（不另收费，2025-10 起可生成事故报告、5 Whys）；Incident Manager 2025-11-07 起不向新客户开放（建议 OpsCenter/合作伙伴）；本账户 90 天内 Revoke/Authorize/ModifySecurityGroup* 事件 3/8/3 次。
- 2026 新事实（第 13 讲）：本账户 AWS Backup 19/19 类型已纳入、DynamoDB 高级功能已开、无备份库/计划；恢复元数据 targetTableName/encryptionType/kmsMasterKeyArn；PITR 保留 1–35 天（provider: recovery_period_in_days）；备份计划规则新增 schedule_expression_timezone、scan_action；价格：Backup DDB 温存储 0.10、恢复 0.15/GB，PITR 0.20/GB·月。
- 2026 新事实（第 12 讲）：原 Security Hub 更名 Security Hub CSPM（API 报错即用此名），新 Security Hub 做暴露 Finding；S3 新桶 2026-04 起默认阻止 SSE-C（巴林、阿联酋除外），Terraform 用 blocked_encryption_types；IAM 模拟器可正确评估桶策略（需 --caller-arn），但对 KMS 密钥策略按通用规则评估（会误报 allowed）；本账户无 GuardDuty/CSPM/Inspector/Macie、无账户级 BPA；KMS 1 美元/月/版本，GuardDuty S3 0.80 美元/百万事件。
- 2026 新事实（第 11 讲）：S3 通用桶 ABAC（2025-11-20，按桶开启，开启后 PutBucketTagging 被拒，改用 TagResource/UntagResource）；PutBucketTagging 整体替换；S3_BUCKET_TAGGED 参数 requiredKeyTags（CSV），不支持 NZ 等区域；CloudTrail Lake 2026-05-31 起不向新客户开放；本账户无 trail、无 Config 记录器、不在 Organizations、0 个桶；Config 0.003/CI、0.001/评估；CloudTrail 额外副本 2.00/10 万、数据事件 0.10/10 万。
- 2026 新事实（第 10 讲）：SSM Agent ≥3.3.40.0 优先 ssmmessages 收命令；DHMC（IMDSv2、Agent ≥3.2.582.0，实例配置文件优先）；本账户 us-east-1 DHMC=$None、受管节点 0；JIT 节点访问 2025-04 GA（0.0137 美元/节点·小时首档）；SendCommand 未注册节点报 InvalidInstanceId；aws:executeAwsApi 单步 ≤25 秒；t4g.nano 0.0042、公网 IPv4 0.005、接口端点 0.01 美元/小时。
- 2026 新事实（第 09 讲）：Logs Insights QL 有 if()/case()，最多 10 个 stats，sort/limit 须在最后一个 stats 之后；计划查询（2025-11，结果到 S3/EventBridge/查找表，事件 `Scheduled Query Completed` 只含元数据）；日志告警 PutLogAlarm（2026）；EventBridge 新 Custom Event Bus（`aws eventsv2`、订阅者、默认重试 300 s/5 次）与 Classic 并存；PutEvents 单次 ≤ 1 MB；SQS 目标可用执行角色；价格用 `aws pricing get-products`（免费、只读）取。

## 截图补拍记录（2026-11-18 控制台会话恢复后完成）

已补拍并插入、重建：09（Logs Insights 查询 + Schedules and alarms 菜单、日志告警表单、EventBridge Sandbox 判定、事件总线页）、10（Fleet Manager、Run Command AWS-RunShellScript、Session Manager 首选项、统一控制台启用页）、11（事件详情、事件 JSON、Config 设置向导）、12（GuardDuty/CSPM/新 Security Hub 入口卡片、S3 建桶 BPA + 默认加密）、13（Backup 区域设置、备份计划窗口）、14（CloudWatch Investigations）、16（IAM 添加 OIDC 提供商）。

未采用：11 的 Config 规则搜索（设置向导的规则搜索只过滤当前页，找不到 s3-bucket-tagged）；14 的 RevokeSecurityGroupIngress 列表（事件均为 root 用户所为，且列表表头在缩放后错位）；10 的 DHMC 开关页（与 Fleet Manager 横幅重复，文件保留在 screenshots/ssm-02-dhmc.jpg）。

截图要点：每次导航后重新注入脱敏脚本（账户号、别名、邮箱、用户名、访问密钥、公网 IP）；Backup 表单默认时区为浏览器本地时区，截图前改为 UTC；CodeMirror 5 编辑器用 `cm.replaceSelection(text,'end','+input')` 写入；离开填过的表单前移除 beforeunload。注意：本账户控制台会话是 root 用户（CloudTrail 可见），最终报告中提醒用户。

### 2026 控制台新事实（截图所见）
- CloudWatch Logs Insights：Schedules and alarms 菜单（Create：Scheduled query / Log alarm）；告警数据源 Metrics / Logs / Alarms，日志告警 = SOURCE 查询 + 聚合表达式 + 阈值 + M/N；CloudWatch Omni（New）。
- EventBridge：现有自定义总线已改称 Classic，规则/存档/重放移到所属总线下；新 Custom 总线用订阅；导航中有 “Scheduled rules (legacy)”。
- Systems Manager：高级实例层取消，混合/多云节点注册免费不限量，自 2026-09-30 起对其使用 Session Manager/Run Command 按次计费；旧版 Session Manager 页 2026-12-31 停用；启用统一控制台会开启 DHMC 检查（每天修正漂移）、每 12 小时清单、每 14 天自动更新 Agent；JIT 节点访问入口先跳转统一控制台启用页。
- Config 向导：按资源类型设频率；全部同频无上限，至少一个 Continuous 时最多 100 个 Daily 类型。
- GuardDuty：30 天试用，AWS Backup 恶意软件防护无试用；新 Security Hub 入口写明旧版已更名 CSPM，基础能力 30 天试用。
- S3 建桶页：默认加密只有 SSE-S3 / SSE-KMS / DSSE-KMS，Bucket Key 默认启用，无 SSE-C 选项。
- AWS Backup：新增 S3 backup tiering、Access points、Search、Malware protection、Restore testing、Legal holds；可纳入 Aurora DSQL、EKS。
- CloudWatch investigations 位于 AI Operations，首次使用需“为账户配置”。

## 发布（2026-11-18）

- 仓库整理：重写前的 19 讲原版 PDF 移到 `archive/original-pdfs/`；新增仓库根 `README.md` 与 `.gitignore`；
  清理各实验的 `.terraform/`（provider 缓存，合计约 13 GB）、`__pycache__/` 与 `chapters/*/build/`。
- `tools/console_prep.js` 改为占位模板，真实替换表只保存在本机 `*.local.*` 文件中。
- `tools/package.py` 生成并逐字节校验两个 ZIP；`tools/test_all.sh` 运行全部离线测试。
