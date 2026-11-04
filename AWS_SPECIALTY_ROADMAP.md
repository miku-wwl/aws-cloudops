# AWS Enterprise Infrastructure & Cloud Operations — 学习与实战路线图（2026 V2）

> **仓库：** [`miku-wwl/aws-cloudops`](https://github.com/miku-wwl/aws-cloudops)  
> **JD 标杆：** [SG Consulting Limited — AWS Senior Cloud Infrastructure Engineer / Architect（Auckland）](https://nz.linkedin.com/jobs/view/aws-senior-cloud-infrastructure-engineer-at-sg-consulting-limited-4461019538)  
> **更新：** 2026-11-05  
> **当前状态：** `PLANNED / NOT RUN`；本仓库尚无真实 AWS 实验、Terraform 运行和恢复验证。  
> **已有基础：** AWS Solutions Architect – Professional、AWS Developer – Associate、Terraform Professional、Kubernetes/CKAD、Java 后端工程。重点是把架构和证书知识转化为企业基础设施实操能力，**不是再考入门证书**。

## 1. 深度解读 SG Consulting 的 Senior AWS JD

该职位是 **架构 + 基础设施实施 + 生产运营 + 技术治理** 结合的高级职位，不是纯 EKS/SRE，也不是只负责云资源创建的 Cloud Engineer。JD 要求 **10+ 年基础设施和云工程经验、真实 AWS Landing Zone 管理经验、跨团队技术领导**。本仓库以其技术能力为学习标杆，**不声称满足工作年限或企业生产所有权要求**。

### 对职责逐项拆解

| JD 主题 | 招聘方希望能解决的问题 | 本路线的可验证学习结果 | 优先级 |
|---|---|---|---|
| AWS Landing Zone lifecycle | 如何创建、配置、治理、升级、检查漂移和退役账户？ | 账户/OU/共享服务设计 + 生命周期 runbook；实际部署可选 | **P0** |
| Organizations / Control Tower | 如何管理多账户边界、Account Factory、日志和控制措施？ | Organizations/Control Tower 的架构与治理矩阵 | **P0** |
| Preventive / Detective / Proactive controls | 哪种风险应阻止、检测还是在创建前拒绝？ | SCP/IAM/Config/Control Tower controls 分工及 allow/deny 证据 | **P0** |
| Enterprise Terraform | 如何建立标准模块、State 隔离、PR 审查、变更审批和漂移处理？ | 一套最小 IaC 实验及受控 delivery 设计 | **P0** |
| AWS network / hybrid | VPC 与 TGW/PrivateLink/Route 53 Resolver 如何组合？故障如何定位？ | 真实 VPC 故障 RCA + 企业混合网络 ADR | **P0/P1** |
| Security and audit | 如何落实 IAM、KMS、CloudTrail、Config、threat detection、secrets？ | 权限矩阵、变更时间线、集中审计与威胁检测设计 | **P0/P1** |
| Production operations | 如何建立告警、定位事故、恢复服务并降低重复故障？ | CloudWatch 查询、告警、两份 RCA 和 Runbook | **P1** |
| HA / DR | Multi-AZ/Multi-Region 什么时候必要？RPO/RTO 是否可实现？ | DR 设计 + 一次有数据校验的真实恢复 | **P1** |
| FinOps | 可靠性、安全与成本如何权衡？ | 费用模型、标签成本分配、实验 teardown 账单复核 | **P1** |
| Technology leadership | 能否解释技术取舍并建立标准、审查与运维流程？ | HLD/LLD、ADR、复盘和审查清单 | **跨模块** |
| AFT / LZA / CfCT / EKS | 何时采用成熟方案，何时不应该引入？ | 比较与选型；不强制部署高成本企业组件 | **P2** |

**岗位来源与性质：** [LinkedIn 原始 JD](https://nz.linkedin.com/jobs/view/aws-senior-cloud-infrastructure-engineer-at-sg-consulting-limited-4461019538)。其列出 AWS Control Tower、Organizations、SCP、Config、Terraform、TGW、Direct Connect、VPN、IAM/KMS、CloudTrail、Security Hub、GuardDuty、Inspector、HA/DR、FinOps 等；LZA、CfCT、AFT、企业级 EKS 属于 desirable，不应全部升级为必做项目。

## 2. 与 KPCP、Azure CloudOps 的边界

- **KPCP：** Kubernetes Controller / Terraform orchestration / 变更审批 / 基础设施生命周期；不重做第二套控制平面。
- **`azure-cloudops`：** Azure Landing Zone、VNet/Private DNS、Azure Policy、Entra ID、Monitor/KQL、恢复。
- **`aws-cloudops`：** Organizations/Control Tower/SCP、AWS Network/IAM、Terraform 交付实践、CloudTrail/Config/CloudWatch、账户治理与故障恢复。
- **EKS：** 有需要时验证与账户权限/网络/审计的集成；不是此仓库的主要工程交付。

**原则：** 各云保留各自的服务差异。AWS SCP ≠ IAM Policy ≠ AWS Config；CloudWatch Logs Insights QL ≠ Azure KQL。架构设计、静态测试、模拟器验证与真实云部署必须分别标注。

## 3. 最高优先级：企业 Landing Zone 参考设计

### 3.1 多账户设计示例（设计任务，不代表已部署）

```text
AWS Organizations / management account
├── Security OU
│   ├── log-archive account
│   └── audit / security-tooling account
├── Infrastructure OU
│   ├── network / connectivity account
│   └── shared-services account (optional)
├── Workloads OU
│   ├── non-production workload account(s)
│   └── production workload account(s)
└── Sandbox OU
    └── time-limited experiment account(s)
```

这是一个用于讨论职责和隔离边界的**参考拓扑**，不是必须创建的账户清单。AWS 建议以账户作为关键隔离边界，并针对 Security、Infrastructure、Workloads、Sandbox 等用途设计 OU；实际结构随组织规模和需求调整。

设计时必须回答：

1. 管理账户为何不承载普通业务？哪些操作由 delegated administrator 承担？
2. Log Archive 与 Security Tooling 如何分工？CloudTrail 组织级聚合与单账户 Event History 的区别是什么？
3. 开发/生产为什么分账户而不是只分 VPC？什么需要共享，如何控制跨账户信任？
4. 哪些基线由 Control Tower 管理，哪些由 Account Factory / AFT / 自定义 Terraform 提供？
5. 新账户申请、初始配置、身份接入、Region 策略、检测漂移、例外审批、退役如何设计？
6. 何种情况下不应部署完整 Control Tower/LZA，而先用单账户沙箱验证技术路径？

**至少两条 ADR：** `ADRs` 可以直接写在 Roadmap 的学习记录中，未来确实需要时再新增文件。例如 `OU/account boundaries`、`Centralized vs distributed networking`、`SCP vs Config control choices`。

### 3.2 必须分清的治理机制

| 机制 | 正确理解 | 常见误区 |
|---|---|---|
| IAM identity/resource policies | 授予或拒绝具体主体对资源/操作的权限 | 以为它自动覆盖整个组织所有账户 |
| SCP (Organizations) | 给成员账户内主体的权限设置上限；**自身不授予权限** | 以为 SCP 的 Allow 就给了 IAM 权限，或以为限制管理账户 |
| RCP | 对支持资源/服务的资源侧权限施加组织级边界；需核对适用范围 | 认为与 SCP 完全等价 |
| Control Tower preventive controls | 预防型控制，可能由 SCP/RCP 等实现 | 认为所有 preventive 都只靠 SCP |
| Control Tower detective controls | 基于 AWS Config 等检测不合规状态 | 认为检测一定会自动阻止资源创建 |
| Control Tower proactive controls | 在支持的 CloudFormation 资源创建流程中预先检查 | 认为任意 API/Terraform 请求都必定受相同 hook 覆盖 |
| CloudTrail | 审计 API/管理活动；Event History 默认单账户单 Region 最近 90 天管理事件 | 认为 Event History 是完整跨账户数据事件审计仓 |
| AWS Config | 资源配置/合规记录与规则，可能产生持续费用 | 以为它能替代 CloudTrail 行为审计 |

**安全规则：** 在没有独立可恢复的实验组织和明确授权时，**禁止**对现有组织根或共享 OU 注入 SCP `Deny`，不得修改 Control Tower 管理的控制资源进行破坏性测试。SCP/IAM 语义可以先做文档推演、官方样例/安全检查；只有权限与隔离边界确认后才做 live allow/deny。

参考：[Multi-account whitepaper](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html) · [SCP semantics](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html) · [Control Tower controls](https://docs.aws.amazon.com/controltower/latest/userguide/how-controls-work.html) · [CloudTrail Event History](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html)

## 4. 专项模块（沿用 A01–A08，新增 A00/A09/A10）

### A00 — Multi-account Landing Zone & Account Lifecycle（新增，P0）

**范围：** Organizations、OUs、Control Tower、Account Factory、Identity Center、Log Archive、Security Tooling、Shared Services、控制措施、账户生命周期。

**任务：** 设计上面所示拓扑，绘制账户间身份/日志/网络路径；对账户 `request → provision → baseline → enroll/govern → monitor/drift → decommission` 制作运行手册，区分哪些环节需要人工审批、哪些由 AWS 托管服务负责。

**验收：** 1 份参考架构、账户/OU 责任矩阵、2 条 ADR、基线/漂移/退役流程。仅设计则状态为 `DESIGNED`，不能标记 `AWS_VERIFIED`。

**官方入口：** [AWS Organizations](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_introduction.html) · [Control Tower](https://docs.aws.amazon.com/controltower/latest/userguide/) · [Organizing multi-account environments](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html)

### A01 — AWS Architecture & Well-Architected（P1）

**范围：** Operational Excellence、Reliability、Security、Performance、Cost Optimization、Sustainability；工作负载职责边界和 SLO/恢复设计。

**任务：** 选一个小型 API/S3/EC2/Lambda 参考工作负载，设计正常请求、身份、日志和故障路径，解释单区、多 AZ、Multi-Region 的收益和成本。

**验收：** 1 份设计评审，包含非功能需求、错误预算/可靠性假设、RTO/RPO 目标和 2 个风险权衡。不声称完成 AWS 正式 Well-Architected Review。

**官方入口：** [Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)

### A02 — VPC Networking & Connectivity Diagnostics（P0）

**范围：** VPC/Subnet、Route Table、SG/NACL、IGW/NAT、VPC Endpoints、Route 53/DNS、Reachability Analyzer、VPC Flow Logs。

**任务：** 在已授权小型沙箱建立正常连接基线，然后有意引入一条可逆的 SG/路由/DNS/endpoint 配置问题。按 `DNS → 路由 → SG/NACL → endpoint/service policy → IAM → 应用响应` 形成排障记录。注意：**S3 Gateway Endpoint 和 Interface Endpoint/PrivateLink 的路径、费用及 DNS 机制不同**。

**验收：** 一次不查看答案的独立诊断，提供原始探针、故障证据、具体根因、同一探针的恢复验证和清理记录。

**官方入口：** [AWS Networking Workshop](https://catalog.workshops.aws/networking/en-US) · [Reachability Analyzer](https://docs.aws.amazon.com/vpc/latest/reachability/what-is-reachability-analyzer.html)

### A03 — IAM, STS & Federated Identity（P0）

**范围：** IAM policies、STS/AssumeRole、cross-account trust、permissions boundaries、IAM Identity Center、IAM Access Analyzer、KMS 和 Secrets Manager 的访问边界。

**任务：** 在隔离账户验证最小权限 IAM `AccessDenied → 分析 → 精准修复 → 重测`。另设计一份跨账户 access path，明确身份策略、信任策略、资源策略、SCP 对有效权限的共同影响。

**验收：** 权限矩阵、失败/成功 API 调用、CloudTrail 佐证、最小权限修复说明。若无真实 Organizations，SCP 层只能是设计/离线分析，不能报告 live SCP test。

**官方入口：** [IAM Access Analyzer](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html) · [Policy validation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-validation.html)

### A04 — CloudWatch, Logs Insights QL & Observability（P1）

**范围：** CloudWatch Metrics/Alarms/Logs、Logs Insights QL、CloudTrail management events、EventBridge、监控告警负责人和噪声控制。

**任务：** 用一个小型可停止的测试负载产生真实日志，写 5 条查询（错误率、延迟、时间聚合、异常来源、变更前后对照）；触发 1 条真正可观测的 Alarm → 记录检查 → 恢复正常状态。

**验收：** 查询及数据来源、实际查询结果、告警时序、误报风险和清理记录。CloudWatch Logs Insights QL **不是 SQL，也不是 Azure KQL**，不要只按扩展名 `.sql` 分类。

**官方入口：** [Logs Insights examples](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-examples.html) · [CloudWatch Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)

### A05 — Systems Manager & Operational Automation（P1）

**范围：** AWS CLI / boto3、Systems Manager Inventory、Session Manager、Run Command、State Manager、Automation、patching/runbooks。

**任务：** 先研究 AWS Cloud & Hybrid Operations Workshop，再写一份只读、限定 Account/Region 的盘点/巡检脚本；为无权限、API 异常、分页、空资源、节流处理编写离线测试。任何修改型 Run Command / Automation 都单独审批并明确 Target。

**验收：** 只读脚本通过离线测试；有授权时再附脱敏 AWS 输出。不得把模拟测试报告成 AWS 运行成功。

**注意：** Systems Manager Incident Manager 和 Change Manager 在 2025 年 11 月停止接纳新客户，旧 Workshop 涉及的启用步骤不能作为新账号实操门槛。

**官方入口：** [AWS Cloud and Hybrid Operations Workshop](https://github.com/aws-samples/aws-cloud-and-hybrid-operations-workshop) · [Incident Manager availability](https://docs.aws.amazon.com/incident-manager/latest/userguide/incident-manager-availability-change.html)

### A06 — Cloud Governance, Audit & Security Operations（P0）

**范围：** SCP / RCP 概念、Control Tower Controls、AWS Config、组织级 CloudTrail、IAM Access Analyzer、Security Hub、GuardDuty、Inspector、KMS、S3 Block Public Access、标签与成本归属。

**任务：**
1. 建立 `risk → preventive/detective/proactive control → owner → alert/action` 控制矩阵。
2. 用自己账户可访问的 CloudTrail Event History 实际分析一次资源变更的 actor/time/action/result；若只有单账户 Event History，明确其**不等于集中日志架构**。
3. 在权限和费用允许的情况下做一个范围受限的 Config compliance 观察；否则提交规则设计和预估成本。
4. Security Hub/GuardDuty/Inspector/WAF/Shield 先研究各自能力和整合路径，不要求全部启用。

**验收：** 1 份审计时间线，1 份控制矩阵，标明实测/设计的证据类型；不得因为 Config 合规就推断不存在安全事件。

**官方入口：** [Control Tower controls](https://docs.aws.amazon.com/controltower/latest/controlreference/controls.html) · [CloudTrail Event History](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html) · [AWS Config](https://docs.aws.amazon.com/config/latest/developerguide/WhatIsConfig.html)

### A07 — AWS Backup, Restore & Resilience（P1）

**范围：** AWS Backup、EBS snapshot/restore、restore point、AWS Health、Multi-AZ/Multi-Region、RTO/RPO、恢复点保留。

**任务：** 选择一个可承受费用的小型数据对象，完成备份、恢复至**独立目标**和文件校验；记录 backup point、开始结束时间、预期 RPO/RTO 与实测差距；清理 Recovery Points/Snapshots/Storage，复查是否持续收费。

**验收：** 恢复操作真实执行、数据一致性得到验证，保存测得恢复时间；不得只凭备份任务绿色状态宣称恢复成功。跨区域 DR 先设计即可。

**官方入口：** [AWS Backup](https://docs.aws.amazon.com/aws-backup/latest/devguide/getting-started.html)

### A08 — Incident Response, RCA & Runbooks（P1）

**范围：** detect → triage → contain → diagnose → recover → validate → RCA；CloudWatch/CloudTrail、变更追踪、风险通报与复盘。

**任务：** 选 2 类隔离环境故障，如 `E01 VPC path failure`、`E02 IAM AccessDenied` 或 `E03 CloudWatch 5xx alert`，逐项记录观察到的事实、排除的假设、操作时间线、回滚和预防措施。安全响应 Playbook 只是参考，不代表真正处理了企业安全事故。

**验收：** 2 份不同类型 RCA；至少一份具有真实 AWS 故障恢复证据；最终 Portfolio Ready 需两项均完成真实隔离验证。

**官方入口：** [AWS incident-response playbooks](https://github.com/aws-samples/aws-incident-response-playbooks)

### A09 — Enterprise Terraform & Controlled Delivery（新增，P0）

**范围：** Terraform AWS Provider、version pinning、reusable modules、remote state + locking、environment separation、CI validation、OIDC federation、Plan review、drift detection、rollback/teardown。

**任务：**
1. 只写一个可回收的最小 VPC/Subnet/SG 或 S3 demo。解释模块接口、版本固定、`terraform fmt -check` / `validate` 与 provider 配置。避免为了演示多账户架构而强制创建多个账户。
2. 设计 `PR → static checks/scan → reviewed plan → explicit approval → restricted apply → post-deploy validation → destroy` 工作流，区分 Plan 和 Apply 的身份、权限及环境。临时身份/OIDC 优先于静态密钥。
3. 明确 state 存储、加密、访问控制、锁定策略、备份/恢复、State 中的敏感值及不提交哪些文件。**锁定能力取决于所用后端/版本配置，不可一概假设已启用**。
4. 设计 drift 和故障回滚：某些 Terraform 变更无法简单通过重新 apply 逆转，需预先保留安全恢复步骤。

**验收：** 真实执行过的 `fmt`/`validate`/`plan`/`apply`/`destroy` 逐项列证据；没权限执行 Apply 时保持 `NOT RUN`。CI 静态通过不等于安全的 live deployment。

**官方入口：** [Terraform on AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/introduction.html) · [AWS OIDC for GitHub](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)

### A10 — Enterprise Networking, AFT & Advanced Platform Patterns（新增，P1/P2）

**范围：** TGW vs VPC Peering、PrivateLink vs VPC Endpoints、Route 53 Resolver、VPN/Direct Connect、集中式出口/inspection、Account Factory vs AFT vs CfCT vs LZA、EKS account boundaries。

**任务：**
- **企业网络：** 设计一个多 VPC/混合网络 HLD，列出 DNS 转发、路由传播、故障域、流量费用和安全边界；避免为学习强行部署 TGW/Direct Connect。
- **AFT：** 学清 AFT 管理账户、account request、provisioning、global/account customizations、GitOps 和 plan-only；记录与普通 Terraform module 的区别。
- **CfCT/LZA：** 说明何时为组织定制部署 Controls/Account Baselines，何时在受监管场景采用 LZA；不需要把三个产品都安装一遍。
- **EKS/ECS：** 了解容器平台在网络、身份、日志和多账户治理中的接入点，把深入 Kubernetes Control Plane 留给 KPCP。

**重要版本/区域说明（核对于 2026-11-05）：** AFT 在 2026-09-16 增加了 account customization `plan_only` 能力；**Asia Pacific (New Zealand) `ap-southeast-6` 不在 AFT 支持部署区域中**，不要默认选择新西兰 Region 部署 AFT。以 AWS 最新区域支持清单为准。

**成本说明：** AWS 官方 LZA 示例（配合 Control Tower，美东 us-east-1，无实际工作负载）估算约 **US$430.22/月**，并非固定报价，更不是免费沙箱。**不要为完成本路线强制部署 LZA、TGW、Network Firewall、Direct Connect 或多账户全天候日志治理栈。**

**官方入口：** [AFT overview](https://docs.aws.amazon.com/controltower/latest/userguide/aft-overview.html) · [AFT 2026 change](https://docs.aws.amazon.com/controltower/latest/userguide/2026-all.html) · [AFT Region limitations](https://docs.aws.amazon.com/controltower/latest/userguide/limits.html) · [LZA guide](https://docs.aws.amazon.com/solutions/latest/landing-zone-accelerator-on-aws/) · [AWS networking](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html)

## 5. 四个 Sprint（学习组织顺序，不是假定完成时间）

| Sprint | 核心模块 | 产出与 gate |
|---|---|---|
| **S1 — Enterprise Foundation** | A00 + A01 + A03/A06 设计 | 多账户架构、账户生命周期、2 条 ADR、SCP/IAM/Config 控制矩阵；`DESIGNED` |
| **S2 — IaC & Networking** | A09 + A02 + A10 设计 | 最小 Terraform 实验、State/CI 审查、一次真实 VPC 故障诊断；按实际步骤标记 `STATIC_CHECK_PASS` / `AWS_VERIFIED` |
| **S3 — Operations & Governance** | A03 + A04 + A05 + A06 + A08 | IAM AccessDenied、CloudTrail 时间线、5 条 Logs Insights 查询、告警、只读巡检、第二份 RCA |
| **S4 — Recovery & Portfolio** | A07 + A08 汇总 + FinOps | Backup/Restore 校验、成本与清理清单、脱敏 HLD/LLD、岗位技能覆盖复盘；全部 mandatory 通过才为 `PORTFOLIO_READY` |

**优先级策略：** 如果只能选最有面试说服力的内容，完成 **A00 架构设计 + A09 Terraform + A02 网络事故 + A06 治理审计 + A08 RCA**。AFT/LZA/TGW/Direct Connect 大型部署均非必做。

## 6. 三个可复现的核心案例

### E01 — VPC 连通性中断

1. 建立最小测试拓扑和成功连接探针；记录源/目标、安全组、路由、DNS 与预期。
2. 在授权的隔离资源内引入单一、可逆错误，禁止触及共享网络。
3. 从现象出发提出至少两种假设，调用 Reachability Analyzer/Flow Logs/CLI 中实际可用的工具验证。
4. 精确恢复原始配置，对比同一探针结果；写出根因与预防措施。
5. 删除有费用的实验组件，核查日志保留和残留资源。

### E02 — IAM AccessDenied / SCP policy reasoning

1. 创建或使用已授权的临时测试角色，确认身份与目标动作。
2. 验证权限不足的失败 API，结合 IAM/资源策略/信任策略的评估路径分析。
3. 在**必要且范围有限**的情况下修复 IAM 规则并重测；保留失败与成功证据。
4. 单独写 SCP 的适用范围/限制推演。除非独立组织和安全回退已验证，否则**不创建真实 SCP Deny 实验**。

### E03 — Backup-to-Restore + Incident Evidence

1. 选定可核验的测试数据和目标 RPO/RTO，建立短期恢复点。
2. 真实恢复到独立资源，比较 checksum/记录数等，记录耗时。
3. 记录期间监控信号、对用户可能的影响、恢复确认与剩余风险。
4. 清理恢复目标和仍可能计费的恢复点，并附复核结果。

## 7. 执行证据等级与安全边界

| 状态 | 可以声称 | 不可以声称 |
|---|---|---|
| `PLANNED` | 明确目标和实验计划 | 已完成实践 |
| `DESIGNED` | 有 HLD/ADR、策略/网络/成本设计 | AWS 已实施 |
| `OFFLINE_PASS` | 本地脚本/Policy 文本或模拟器检查通过 | 等于 AWS 实测 |
| `STATIC_CHECK_PASS` | 格式/静态检查成功 | Terraform Apply 成功 |
| `AWS_DEPLOYED` | 在授权 AWS 中完成实际部署 | 已完成故障、性能/恢复验收 |
| `AWS_VERIFIED` | 同一环境中的目标行为有独立实测证据 | 生产环境规模或 On-call 经历 |
| `RECOVERED` | 故障或数据恢复并已验证 | RPO/RTO 必然达标（除非测量证明） |
| `CLEANED_UP` | 检查残留/保留与相关费用已记录 | 后续账单绝不再产生 |
| `BLOCKED` / `NOT_RUN` | 没有条件或尚未执行 | PASS |

**每项有费实操前：** 确认账号归属、Region、IAM 权限、每项资源单价、费用上限与人工停止条件；Budgets 是告警，不是自动硬限额。

**禁止事项：** 生产/雇主/共享账户故障注入；在组织根直接试危险的 Deny；提交 IAM 凭据、敏感状态文件、真实账号/用户标识、原始 CloudTrail 客户日志；未运行却编造命令输出、证书、截图或性能结果。

**CloudTrail 低成本优先：** Event History 默认可在单账户单 Region 查看过去 90 天管理事件，无需为这个最低门槛启用新的长期组织级日志架构。它不含默认 data events，也不提供跨账户聚合。

**尽量避免：** 长期开启 NAT Gateway、TGW、Network Firewall、LZA、Config Recorder、大量日志摄取和跨区域复制；即使资源未被主动使用，也可能产生费用。费用与功能规则需实验当天查 AWS 官方文档。

## 8. Definition of Done / 求职证据包

- [ ] 参考 OU/Account/Landing Zone 图 + 两条 ADR + Account lifecycle runbook。
- [ ] SCP / IAM / Config / Control Tower 控制类型分工矩阵和权限边界证明。
- [ ] 最小 Terraform IaC 方案；明确 `fmt`、`validate`、`plan`、`apply`、`destroy` 各项的真实执行结果和 State 方案。
- [ ] 一个真实 AWS VPC 网络故障案例：基线、诊断、恢复与 RCA。
- [ ] 一项实际 IAM allow/deny 验证 + CloudTrail 事件时间线；SCP 真实验证非硬性要求。
- [ ] 五条真实可运行的 CloudWatch Logs Insights 查询和一次已触发的 Alarm。
- [ ] 一份默认只读的 AWS 资源巡检脚本，有离线测试及授权 AWS 输出。
- [ ] 两份不同类型的隔离环境 Incident RCA，至少覆盖网络和身份/告警，并有真实 AWS 证据。
- [ ] 一次真实 Backup **and Restore**，校验数据完整性，记录实测时间与 RPO/RTO 的差距。
- [ ] 成本预估、权限与敏感信息检查、销毁后资源核查、费用复盘。

**最终状态：** 以上核心 mandatory 项（不含完整 Control Tower/LZA/AFT/TGW 部署）实证完成后才标记 `PORTFOLIO_READY`。当前全部是 `PLANNED / NOT RUN`。设计与验证可以分阶段完成，不能拿真实工作经历无法证明的技能包装成“生产多年管理过 Landing Zone”。

## 9. 官方资料入口（自己搜索深入教程即可）

| 方向 | AWS 官方文档/Workshop |
|---|---|
| Enterprise multi-account | [Organizing Your AWS Environment](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html) |
| Control Tower | [User Guide](https://docs.aws.amazon.com/controltower/latest/userguide/) · [Controls](https://docs.aws.amazon.com/controltower/latest/controlreference/controls.html) |
| SCP / Organizations | [SCP concepts](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html) |
| AFT / Region support | [AFT overview](https://docs.aws.amazon.com/controltower/latest/userguide/aft-overview.html) · [Limitations](https://docs.aws.amazon.com/controltower/latest/userguide/limits.html) |
| LZA | [Landing Zone Accelerator](https://docs.aws.amazon.com/solutions/latest/landing-zone-accelerator-on-aws/) |
| Terraform delivery | [AWS Terraform best practices](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/introduction.html) |
| Network | [AWS Networking Workshop](https://catalog.workshops.aws/networking/en-US) · [Reachability Analyzer](https://docs.aws.amazon.com/vpc/latest/reachability/what-is-reachability-analyzer.html) |
| IAM | [IAM Access Analyzer](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html) |
| CloudWatch | [Logs Insights examples](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-examples.html) |
| CloudTrail | [Event history limitations](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html) |
| Operations | [AWS Cloud and Hybrid Operations Workshop](https://github.com/aws-samples/aws-cloud-and-hybrid-operations-workshop) |
| Incident | [AWS Incident Response Playbooks](https://github.com/aws-samples/aws-incident-response-playbooks) |
| Backup | [AWS Backup](https://docs.aws.amazon.com/aws-backup/latest/devguide/getting-started.html) |

*本路线为个人独立编排的学习计划，不是 AWS 官方课程。SG Consulting 的 JD 用作技能抽取标杆，不代表该公司参与编写了本项目。*
