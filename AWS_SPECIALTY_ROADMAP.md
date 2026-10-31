# AWS Cloud Operations & Incident Response — 专项训练路线图

> 编制日期：2026-10-31（NZDT）  
> 状态：**PLANNED / NOT RUN**  
> 适用目标：新西兰 AWS Cloud Engineer、CloudOps、SRE、Platform Engineer 面试与可复现实操证据。  
> 原则：这不是第三个大型云平台；它是 KPCP 以外的 AWS 专项技能训练与工程证据仓库。

## 0. 项目定位与已有基础

- **固定 Project 1：KPCP** —— Go、Kubernetes、Terraform、变更审批、资源生命周期。其主要既有验收为 Kind + LocalStack，本路线不能把它们冒充为真实 AWS 生产运行。
- **可替换的简历 Project 2 展示位置：AWS Cloud Operations & Incident Response** —— AWS 的运行、网络排障、身份审计、监控、故障处理和恢复能力。只有完成真实实验后才能写成已完成项目。
- **通用 Java / Full Stack 岗位**则优先展示 LedgerCore，而不是把 AWS 专项强行塞进所有简历。
- 已持有 AWS SAP、DVA 等证书，学习重点不是再堆认证，而是实操、证据、运行手册与技术判断。

## 1. 来源真实性与限制（非常重要）

| 来源类别 | 举例 | 如何使用 |
|---|---|---|
| AWS 官方课程与认证 | AWS Skill Builder、Cloud Operations on AWS、CloudOps Engineer SOA-C03、Microcredentials | 官方学习与能力评估来源；部分需要订阅、培训机构或注册 |
| AWS Workshop / 官方文档 | AWS Networking Workshop、IAM Access Analyzer Workshop、CloudWatch Logs Insights、AWS Backup | 按官方文档执行真实或引导式实操，可能产生费用 |
| AWS 官方账号开源示例 | `aws-samples/aws-cloud-and-hybrid-operations-workshop`、`aws-samples/aws-incident-response-playbooks` | 真实公开仓库，但示例不是经过生产验证的万能方案，不等于 AWS 服务正式文档 |
| **本仓库自行设计的内容** | 三周节奏、故障注入、8 项专项、验收 Gate、RCA 模板 | **不是 AWS 官方课程**；必须自己执行、记录并独立验证 |

### 重要版本陷阱

AWS Systems Manager **Incident Manager** 与 **Change Manager** 已自 **2025-11-07** 起停止对新客户开放。旧 Workshop 中要求新开户启用它们的章节不能照抄。使用现行的 CloudWatch、EventBridge、Systems Manager Automation/OpsCenter 和人工响应流程实现相关教学目标，不要将其包装成 AWS 官方替代课程。

- [Incident Manager availability change](https://docs.aws.amazon.com/incident-manager/latest/userguide/incident-manager-availability-change.html)
- [Change Manager availability change](https://docs.aws.amazon.com/systems-manager/latest/userguide/change-manager-availability-change.html)

## 2. 与 Azure 专项的对照

| Azure 专项 | AWS 对应专项 | 期望掌握 |
|---|---|---|
| AZ-305 Case Studies | AWS Well-Architected — Operational Excellence / Reliability | 架构设计、可靠性、RTO/RPO 与权衡 |
| AZ-700 Networking | AWS Networking Workshop、Reachability Analyzer | VPC、SG、NACL、Route Table、Endpoint、DNS |
| Entra / RBAC | IAM、STS、IAM Access Analyzer | 权限设计与 AccessDenied 排查 |
| Azure Monitor / KQL | Amazon CloudWatch / Logs Insights QL | 指标、告警、日志查询、故障观察 |
| Azure PowerShell Automation | AWS CLI / Python boto3 / Systems Manager | 运维脚本、SSM、状态维护 |
| Azure Policy | AWS Config / CloudTrail | 配置偏离、审计与合规检查 |
| Azure Backup | AWS Backup / EBS restore | 灾备演练与数据恢复验证 |
| Azure Applied Skills | AWS Microcredentials | 有监督的动手操作能力验证 |

## 3. 八大专项模块（官方链接 + 自定义验收）

### A01 — AWS Architecture & Operational Excellence

**官方资源**
- [AWS Operations training and Cloud Operator Ramp-Up Guide](https://aws.amazon.com/training/learn-about/operations/)
- [AWS Well-Architected Reliability Pillar](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/)
- [AWS Certified CloudOps Engineer – Associate (SOA-C03)](https://aws.amazon.com/certification/certified-cloudops-engineer-associate/)

**训练任务（自定义）**：选一个小型单区域 Web/API 工作负载，写出架构图、故障模式、可观测信号、成本边界、RTO/RPO 目标。先写假设，再运行实验，不再重新开发 IaC 控制器。

**Gate A01**：1 份架构决策记录，明确设计权衡及未验证事项。

### A02 — VPC Networking & Connectivity Troubleshooting

**官方资源**
- [AWS Networking Workshop](https://catalog.workshops.aws/networking/en-US)
- [AWS VPC Reachability Analyzer 官方文档](https://docs.aws.amazon.com/vpc/latest/reachability/what-is-reachability-analyzer.html)
- [Observing and Diagnosing Your Network on AWS — Reachability Analyzer Lab](https://catalog.workshops.aws/workshops/cf2ecaa4-e4be-4f40-b93f-e9fe3b1c1f64/en-US/vpcreachabilityanalyzer/module2)

**训练任务（自定义）**：在隔离 AWS 环境部署最小 VPC + 受控测试连接；有意引入一个错误 SG 或 Route Table 条目；用 Reachability Analyzer、VPC Flow Logs、CLI 验证阻断点并恢复。

**Gate A02**：一份连通性诊断报告，包含预期与实际路径、根因、修复证据与清理记录。

**费用注意**：EC2、NAT Gateway、Flow Logs、Reachability Analyzer（按分析收费）、某些网络设备均可能收费；跳过高成本模块如 Network Firewall 或 TGW。

### A03 — IAM, STS & Least Privilege

**官方资源**
- [AWS IAM Access Analyzer Policy Validation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-validation.html)
- [Integrating IAM Access Analyzer into CI/CD Pipeline — Workshop](https://catalog.workshops.aws/accessanalyzercicd)

**训练任务（自定义）**：创建最小权限的沙箱角色，演示受限资源操作的 `AccessDenied`；用 IAM Policy Simulator / Access Analyzer 的适用功能分析并修复；记录 CloudTrail 证据。避免创建或共享长效 IAM 用户密钥。

**Gate A03**：权限矩阵、Policy JSON（不含身份秘密）、错误与成功测试，以及保留最小权限的解释。

**费用注意**：普通 Policy Validation 与某些 Custom Policy Checks 的收费规则不同，操作前确认当前 AWS 计费规则。

### A04 — CloudWatch, Logs Insights & Alerting

**官方资源**
- [CloudWatch Logs Insights QL tutorials](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData_Tutorials.html)
- [CloudWatch Logs Insights sample queries](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-examples.html)

**训练任务（自定义）**：为最低成本的测试负载产生日志；完成五类 Logs Insights QL 查询（异常、延迟分布、按时间窗错误率、错误来源、部署前后对比），并配置一条能够通过控制测试实际触发的告警。

**Gate A04**：5 份保存的 `.sql` 或 `.txt` Logs Insights 查询、1 份告警验证截图和警报降噪说明。

**区别于 Azure KQL**：Logs Insights QL 是 AWS 自有的日志查询语言，**不是 KQL**；运行官方教程通常需要账户里先有 CloudWatch Logs 数据，不能假定和 Azure 免费 Log Analytics Demo 一样开箱即用。

### A05 — Systems Manager & Operational Automation

**官方资源**
- [Cloud and Hybrid Operations Workshop（Episode 1 / 4）](https://github.com/aws-samples/aws-cloud-and-hybrid-operations-workshop)
- [State Manager + CloudWatch Agent Exercise](https://github.com/aws-samples/aws-cloud-and-hybrid-operations-workshop/blob/main/episode-01-step-04-enable-state.md)

**训练任务（自定义）**：学习 Session Manager、Run Command、State Manager、Inventory 与 Automation 的职责；编写默认只读的 AWS CLI / Python 资源清点脚本，离线测试，并在沙箱验证；选一项预防性维护任务，记录授权和结果。

**Gate A05**：通过离线单元测试的只读脚本，附真实 AWS 输出的脱敏片段及说明；变更动作需单独审批。

### A06 — Governance, Audit & Cost

**官方资源**
- [Cloud and Hybrid Operations Workshop（Episode 2）](https://github.com/aws-samples/aws-cloud-and-hybrid-operations-workshop/blob/main/episode-02-step-01-enable-config-cloudtrail.md)
- [AWS IAM Access Analyzer](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html)
- [AWS Cost Explorer pricing](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/pricing/)

**训练任务（自定义）**：对一个已批准的实验资源，调查 CloudTrail 变更记录和 AWS Config 配置历史；记录标签合规、变更来源及成本清单。AWS Config / CloudTrail 专项功能可能超出免费额度，先做价格检查。

**Gate A06**：1 个变更审计时间线、1 份资源/成本治理报告、无敏感信息上传。

### A07 — AWS Backup, Restore & Resilience

**官方资源**
- [AWS Backup getting started](https://docs.aws.amazon.com/aws-backup/latest/devguide/getting-started.html)
- [Restore an EBS volume](https://docs.aws.amazon.com/aws-backup/latest/devguide/restoring-ebs.html)
- [AWS Fault Injection Service documentation](https://aws.amazon.com/documentation-overview/fis/)

**训练任务（自定义）**：在单个小型独立测试资源上，设置可控恢复点，完成 **restore** 并核对测试文件校验和；记录实际恢复耗时、RPO/RTO 目标与差距。FIS 为可选的高阶实验，禁止在其他人或生产资源上操作。

**Gate A07**：可复现恢复步骤、数据一致性验证、测得的实际恢复时间、清理证据。

### A08 — Incident Response & RCA

**官方资源**
- [AWS Incident Response Playbook Samples](https://github.com/aws-samples/aws-incident-response-playbooks)
- [Building Incident Response Playbooks for AWS — Workshop](https://github.com/aws-samples/aws-incident-response-playbooks-workshop)
- [AWS Incident Response Demonstrated](https://aws.amazon.com/blogs/training-and-certification/march-2026-new-offerings/)

**训练任务（自定义）**：选两项隔离沙箱事故：① 网络不可达 ② IAM 授权失败或应用错误告警。保存时间线、证据、处置步骤、回滚措施、RCA、持续改进方案。官方安全事件 Playbook 的案例可参考，但不必启用全部昂贵的安全服务。

**Gate A08**：2 份完整 RCA + 运行手册，至少一份包含真实 AWS 的故障和恢复验证证据。

## 4. 官方实操能力评估（可选，不要求再考 Associate）

- [AWS Application Networking Demonstrated](https://aws.amazon.com/blogs/training-and-certification/march-2026-new-offerings/)
- [AWS Incident Response Demonstrated](https://aws.amazon.com/blogs/training-and-certification/march-2026-new-offerings/)
- [AWS Microcredentials 官方说明](https://aws.amazon.com/blogs/training-and-certification/microcredentials-from-aws-are-now-free-heres-why-that-matters/)
- [AWS Skill Builder](https://aws.amazon.com/training/digital/)

AWS 官方介绍的这些 Microcredentials 是实时环境中的动手考核，**不是本仓库自行设计的测试**。按 2026 年官方说明可免费参加，但报名入口、资格和有效条件需以 Skill Builder 当时页面为准。

另有 [Cloud Operations on AWS](https://aws.amazon.com/training/learn-about/operations/)（官方课程；Digital Classroom / 讲师授课与订阅权益可能不同），以及受教育机构参与限制的 [AWS Academy Cloud Operations](https://aws.amazon.com/training/awsacademy/)；无需为了这个专项重新上完整入门课程。

## 5. 三周任务安排（本仓库自行编排，非 AWS 官方原始课表）

| 周次 | 模块 | 预期交付物 |
|---|---|---|
| Week 1 | A01 架构、A02 网络、A03 IAM | 架构 ADR、网络排障报告、IAM 权限矩阵与审计证据 |
| Week 2 | A04 CloudWatch、A05 SSM 自动化、A06 Governance | 5 条日志查询、真实告警验证、只读自动化脚本、审计报告 |
| Week 3 | A07 恢复、A08 Incident RCA、Microcredentials | 备份恢复验证、两份 RCA、可选 AWS 官方实操考核结果 |

三周仅为组织顺序，不是进度或完成时长承诺。优先保持低成本，必要时分多次、不同时间执行。

## 6. 自拟故障案例（不是 AWS 官方原版实验）

### E01 VPC Connectivity Incident

- **Hypothesis**：错误的 Security Group 或 Route Table 会阻止符合条件的测试连接。
- **Action**：只修改自己隔离沙箱中的测试资源。
- **Diagnosis**：Reachability Analyzer、VPC Flow Logs、路由检查。
- **Recovery**：恢复基线；测试连接成功。
- **Evidence**：前后状态、CLI 输出、RCA、资源删除记录。

### E02 IAM AccessDenied Incident

- **Hypothesis**：角色权限缺失导致某个预期 API 访问失败。
- **Diagnosis**：CloudTrail + IAM Policy Evaluation + Access Analyzer。
- **Recovery**：仅增加必需动作与资源范围，不授予 AdministratorAccess。
- **Evidence**：权限矩阵、失败及成功 API 调用结果。

### E03 Application Error Alert

- **Hypothesis**：测试 API 的 5xx 上升能够被 CloudWatch 告警发现。
- **Diagnosis**：Logs Insights 查询 + Metric/Alarm 关联。
- **Recovery**：恢复正常版本，确认告警进入正常态；记录误报和检测延迟。
- **Evidence**：时间线与结果，不凭空编造 MTTR。

### E04 Backup & Restore

- **Hypothesis**：隔离资源中的已知测试数据能够从恢复点完整复原。
- **Recovery**：按官方步骤创建独立恢复目标，比较校验和。
- **Evidence**：恢复点、操作记录、数据校验结果与实际耗时。

## 7. 安全、成本与真实性红线

1. 先读官方项目的 Cost / Prerequisite / Cleanup；测试账户必须独立于生产或个人重要资源。
2. 保持短生命周期，不部署高成本服务（NAT Gateway、Network Firewall、Transit Gateway、大型 RDS、长期运行的 GuardDuty/Config/日志摄取），除非任务确实需要且已明确预算。
3. 创建预算告警，但**预算告警不是消费硬上限**。建议人工复查全部计费资源与账单；删除资源后仍要确认后续账单变化。
4. 使用 IAM Role / 临时凭据；禁止在仓库、日志、截图里泄露 Access Keys、Token、真实账号标识、内部 IP/域名或客户数据。
5. `terraform destroy` 不代表所有服务都不再收费；检查 S3、CloudWatch Logs、Backup Vault/Recovery Points、EBS Snapshots、NAT、Config 等是否残留。
6. 线上服务变更与自动化执行默认必须显式审批。不要将实验脚本指向生产账户。
7. 把结果分别标记为 `PLANNED`、`OFFLINE_PASS`、`AWS_VERIFIED`、`BLOCKED`、`NOT_RUN`，不能用 LocalStack 通过来代替真实 AWS 验证。

## 8. 面向新西兰 JD 的技术映射

详见 [`JD_SKILL_MAPPING.md`](JD_SKILL_MAPPING.md)。重点来自 AWS Cloud Engineer / SRE 岗位常见要求：VPC、IAM、Terraform、CloudWatch、Config、Backup、Incident / RCA、Systems Manager、成本管理。这里是技能映射，不表示已满足某个职位的签证或生产工作年限要求。

## 9. 与 KPCP / LedgerCore 的组合

- **Cloud / Platform / AWS SRE 岗**：简历首位 KPCP；AWS CloudOps 实验达到 `AWS_VERIFIED` 后，可用作第二展示项目，强调诊断与运维，而非重复展示 Terraform 控制器。
- **Java / Full Stack 岗**：LedgerCore 首位；KPCP 第二；AWS 专项不必占项目名额。
- **Azure 强相关岗**：KPCP + `azure-cloudops`；不要把 AWS 训练结果说成 Azure 技能。

## 10. 开始前检查表

- [ ] 建立隔离 AWS 沙箱，并记录 Account/Region（脱敏）和允许触及的资源范围。
- [ ] 评估价格、批准预算和清理步骤；记录不部署的高费用模块。
- [ ] 写好 `docs/STATUS.md` 的实际任务和证据目录。
- [ ] 先阅读 AWS Networking Workshop 的 VPC 基础与故障诊断部分。
- [ ] 用 `docs/templates/EXPERIMENT.md` 记录第一项 E01。
- [ ] 只在真实执行后变更 `NOT_RUN` 状态。

## 11. 核心官方资源索引

- [AWS Operations Training](https://aws.amazon.com/training/learn-about/operations/)
- [CloudOps Engineer – Associate](https://aws.amazon.com/certification/certified-cloudops-engineer-associate/)
- [AWS Networking Workshop](https://catalog.workshops.aws/networking/en-US)
- [Reachability Analyzer](https://docs.aws.amazon.com/vpc/latest/reachability/what-is-reachability-analyzer.html)
- [IAM Access Analyzer Workshop](https://catalog.workshops.aws/accessanalyzercicd)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData_Tutorials.html)
- [Cloud and Hybrid Operations Workshop](https://github.com/aws-samples/aws-cloud-and-hybrid-operations-workshop)
- [AWS Backup](https://docs.aws.amazon.com/aws-backup/latest/devguide/getting-started.html)
- [AWS Incident Response Playbooks](https://github.com/aws-samples/aws-incident-response-playbooks)
- [AWS Microcredentials](https://aws.amazon.com/blogs/training-and-certification/microcredentials-from-aws-are-now-free-heres-why-that-matters/)
- [Incident Manager Availability Change](https://docs.aws.amazon.com/incident-manager/latest/userguide/incident-manager-availability-change.html)
- [Change Manager Availability Change](https://docs.aws.amazon.com/systems-manager/latest/userguide/change-manager-availability-change.html)
