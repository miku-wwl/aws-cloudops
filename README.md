# AWS CloudOps 工程教材 · 2026 修订版（V1.0）

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

面向云运维 / 平台 / SRE 工程师的 19 讲 AWS CloudOps 教材。每一讲都从一个真实的排障问题出发，按
**情境 → 机制图 → 分步例题 → 实验 → 故障卡 → 练习与解析** 组织（版式参照《高中物理·加速度》样章），
所有结论都附有可复现的证据：本地模型与单元测试、Terraform 测试与只读 plan、免费的只读 / 计算型 AWS API，
以及已脱敏的真实控制台截图。内容按 2026 年 11 月的 AWS 官方文档与控制台核对。

V1.0 是教材出版版，内容已冻结；在真实 AWS 账户中 apply 的实验留给 V1.1。
V1.1 进行中（状态与费用台账见 [V1.1_PROGRESS.md](V1.1_PROGRESS.md)）：第 02 讲已完成真实 apply → 注入故障 → 恢复 → destroy。

## 下载

| 内容 | 位置 | 大小 |
|---|---|---|
| 19 讲 PDF 合集 | [Release v1.0.0](../../releases/tag/v1.0.0) 附件，或仓库内 [textbook/dist/AWS-CloudOps-19讲-PDF合集-2026-11.zip](<textbook/dist/AWS-CloudOps-19讲-PDF合集-2026-11.zip>) | 36 MB |
| 全部可编辑源稿与实验工程 | 同上，或仓库内 [textbook/dist/AWS-CloudOps-19讲-源稿与实验工程-2026-11.zip](<textbook/dist/AWS-CloudOps-19讲-源稿与实验工程-2026-11.zip>) | 5 MB |
| 单讲 PDF | [textbook/dist/pdf/](textbook/dist/pdf) | 19 个，共 242 页 |

Release 附件名改为 ASCII（GitHub 会改写附件名中的中文），内容与仓库中的两个 ZIP 逐字节相同，SHA-256 见 Release 说明。
在 GitHub 上打开仓库中的 ZIP 后，点击 “Download raw file” 也可下载。两个 ZIP 由 `textbook/tools/package.py` 生成，
并与 `dist/pdf/` 和源稿逐字节校验一致（CI 每次推送都会重新校验）。

## 19 讲目录

| 讲 | 编号 | 标题 | 页数 | PDF |
|---|---|---|---|---|
| 01 | A00-01 | Landing Zone：新账户如何从“能用”变成“受治理”？ | 22 | [PDF](<textbook/dist/pdf/A00-01_Landing_Zone_与_Control_Tower_4.0.pdf>) |
| 02 | A01-01 | 可靠性：怎样证明一个 API“足够可靠”？ | 17 | [PDF](<textbook/dist/pdf/A01-01_Well-Architected_与可靠性.pdf>) |
| 03 | A02-01 | VPC 路由与 NACL：同一个 VPC，为什么仍然连不通？ | 15 | [PDF](<textbook/dist/pdf/A02-01_VPC_路由与_NACL.pdf>) |
| 04 | A02-02 | 安全组：规则写对了，为什么不通？ | 12 | [PDF](<textbook/dist/pdf/A02-02_Security_Group_安全组.pdf>) |
| 05 | A02-03 | DNS 与终端节点：解析成功，为何仍超时？ | 12 | [PDF](<textbook/dist/pdf/A02-03_DNS_与_VPC_终端节点.pdf>) |
| 06 | A03-01 | IAM 与 STS：有 Allow，为何仍被拒？ | 12 | [PDF](<textbook/dist/pdf/A03-01_IAM_评估与_STS.pdf>) |
| 07 | A03-02 | 联邦身份与 KMS：为何读不到秘密？ | 13 | [PDF](<textbook/dist/pdf/A03-02_联邦身份_KMS_与_Secrets.pdf>) |
| 08 | A04-01 | CloudWatch：指标升了，为何不告警？ | 12 | [PDF](<textbook/dist/pdf/A04-01_CloudWatch_指标与告警.pdf>) |
| 09 | A04-02 | Logs Insights × EventBridge：从“查到”到“送达” | 17 | [PDF](<textbook/dist/pdf/A04-02_Logs_Insights_与_EventBridge.pdf>) |
| 10 | A05-01 | Systems Manager：没有 SSH，怎样安全地运维？ | 16 | [PDF](<textbook/dist/pdf/A05-01_Systems_Manager_无SSH运维.pdf>) |
| 11 | A06-01 | CloudTrail × Config：谁改了配置？现在还合规吗？ | 14 | [PDF](<textbook/dist/pdf/A06-01_CloudTrail_与_Config.pdf>) |
| 12 | A06-02 | 安全检测与数据保护：配置合规了，数据就安全吗？ | 11 | [PDF](<textbook/dist/pdf/A06-02_安全检测与数据保护.pdf>) |
| 13 | A07-01 | 备份恢复与灾备：备份“绿了”，为什么业务还是恢复不了？ | 11 | [PDF](<textbook/dist/pdf/A07-01_备份恢复与灾备.pdf>) |
| 14 | A08-01 | 事故响应与根因分析：从现象走到可复核的根因 | 10 | [PDF](<textbook/dist/pdf/A08-01_事故响应与根因分析.pdf>) |
| 15 | A09-01 | Terraform 计划、状态与模块：validate 全绿，为什么还不能 apply？ | 8 | [PDF](<textbook/dist/pdf/A09-01_Terraform_计划_状态_模块.pdf>) |
| 16 | A09-02 | 远程状态、OIDC 与漂移：没有长期密钥，怎样安全地 apply？ | 8 | [PDF](<textbook/dist/pdf/A09-02_远程状态_OIDC_与漂移.pdf>) |
| 17 | A10-01 | TGW、VPN 与企业 DNS：隧道 UP 了，数据库为什么还超时？ | 11 | [PDF](<textbook/dist/pdf/A10-01_TGW_VPN_与企业DNS.pdf>) |
| 18 | A10-02 | Control Tower、AFT 与 LZA：账户已经创建，为什么还不能交付？ | 11 | [PDF](<textbook/dist/pdf/A10-02_Control_Tower_AFT_与_LZA.pdf>) |
| 19 | FIN-01 | FinOps 与成本回收：Destroy 完成，为什么账单还在增加？ | 10 | [PDF](<textbook/dist/pdf/FIN-01_FinOps_成本回收.pdf>) |

## 仓库结构

```
aws-cloudops/
├── README.md                     本文件
├── LICENSE                       Apache License 2.0
├── .gitignore                    构建产物、Terraform 缓存 / 状态、本机敏感文件都不入库
├── .gitattributes                文本文件一律 LF（*.ps1 为 CRLF），保证各平台检出与源稿 ZIP 逐字节一致
├── .github/workflows/ci.yml      离线 CI：ZIP 校验、Python unittest、Terraform fmt / validate / test
├── archive/original-pdfs/        重写前的 19 讲原版讲义（只读存档）
└── textbook/
    ├── README.md                 源稿约定、截图与脱敏方法
    ├── PROGRESS.md               逐讲完成记录、2026 年核对过的新事实、V1.0 封版状态
    ├── tools/                    build.py（Markdown → HTML → PDF → QA）、style.css、figlib.py（机制图）、
    │                             shot.py（截图规范化）、pages.py（逐页审阅）、package.py（打包与校验）、
    │                             test_all.sh（全部离线测试）、console_prep.js（截图前页面内脱敏模板）
    ├── chapters/<编号>/           共 19 个
    │   ├── chapter.md            正文源稿（Pandoc Markdown）
    │   ├── figures/              机制图源码 figs.py 与生成的 SVG（共 81 张）
    │   ├── screenshots/          真实控制台截图（正文使用 53 张，另 3 张备用，均已脱敏）
    │   └── labs/                 实验：README、Python 模型与单元测试、Terraform 与 tests/
    └── dist/
        ├── pdf/                  19 讲 PDF
        └── *.zip                 两个最终 ZIP
```

## 构建

依赖：Python 3.11+（PyYAML、Pygments、Pillow、pypdf）、Pandoc ≥ 3.8、Google Chrome（headless 打印）、
poppler（`pdftoppm`，用于 QA）；字体 Noto Sans SC / Noto Serif SC、Cascadia Mono。

```bash
cd textbook
python tools/build.py A04-01             # 单讲：生成机制图 + HTML + PDF + 自动 QA
for d in chapters/*/; do python tools/build.py "$(basename "$d")"; done   # 全部 19 讲
python tools/package.py                  # 重新生成两个 ZIP，并逐字节校验
python tools/package.py --verify         # 只校验
bash tools/test_all.sh                   # 全部离线测试（--python / --terraform 只跑一部分）
```

## 实验怎样使用

- 每讲的 `labs/README.md` 写明每个实验**会不会改动 AWS、费用多少、验证状态**和运行命令。
- **Python 模型**（路由、IAM 评估、告警、事件匹配、账单分类……）完全离线：`python -m unittest -v`
  （第 07 讲 `02-envelope` 需要 `pip install cryptography`）。
- **Terraform 实验**按三个级别逐级推进，每一级的状态见下一节的表：
  1. **离线测试**：`terraform init -backend=false && terraform test`。tests 全部使用 mock provider，不需要 AWS 凭证，
     不访问 AWS；没有 tests 的根模块只做 `terraform validate`。CI 每次推送都会运行。
  2. **只读 Plan**：在隔离的实验账户中执行 `terraform plan`，只读取账户信息，不创建资源。
     **多数实验的默认 plan 并不是零资源**：plan 列出的就是 apply 时会创建的资源。只有 17-2 与 19-4
     默认 0 个资源，要打开 `enable_paid_lab = true` / `enable = true` 才会创建；18-2 不含任何 AWS 资源。
  3. **实际 Apply**：**V1.0 没有执行任何 apply。** 如需动手，只在隔离的实验账户中进行，结束后立即
     `terraform destroy`，并按各讲 README 复核残留与账单。16-2 的 `compare/` 任何时候都不要 apply。
- 一次运行全部离线测试：`cd textbook && bash tools/test_all.sh`
  （可设 `PLUGIN_DIR=<本地 provider 目录>` 离线安装 provider；结束后可删除各实验下的 `.terraform/`）。

## 实验与验证级别（V1.0 逐个核实）

目录相对于 `textbook/chapters/`。“只读 Plan”是本书对实验账户实际执行的 `terraform plan` 摘要（输出见各讲正文或
实验目录中的 `plan-*.txt`）；“Apply 会创建什么”是按代码与 plan 整理的结果，**V1.0 均未 apply**。

| 实验 | 目录 | 离线测试 | 只读 Plan（本书实测） | Apply 会创建什么（V1.0 未执行） | 费用估算 |
|---|---|---|---|---|---|
| 1-3 | `A00-01/labs/02-landing-zone` | test 5/5 | 未执行：前提是 Organizations 管理账户，本账户不属于任何组织 | Control Tower 着陆区 4.0 与 3 个服务角色 | 持续产生 CloudTrail / Config / S3 费用 |
| 1-4 | `A00-01/labs/03-ou-governance` | validate | 未执行：需要已部署的着陆区 | 2 个 OU，并在 OU 上启用基线与控制 | 依所选控制而定 |
| 1-5 | `A00-01/labs/04-drift-alerts` | validate | 未执行 | EventBridge 规则、SNS 主题与邮件订阅 | 近似 0 |
| 2-2 | `A01-01/labs/02-lambda-reliability` | test 6/6 | 10 to add | Lambda 函数、日志组、IAM 角色与策略、燃烧率告警与复合告警 | Lambda 在免费额度内；告警约 2 美元/月（按小时折算） |
| 2-4 | `A01-01/labs/03-fis-experiment` | validate | 未执行：需要 2-2 apply 后的 `function_arn`、`stop_alarm_arn`、`config_bucket` | FIS 实验模板、IAM 角色与策略、S3 配置桶 | 约 2 个 FIS 动作分钟 |
| 3-2 / 3-3 | `A02-01/labs/02-vpc-lab` | test 6/6 | 12 to add；`enable_instances=true` 时 28 | VPC、子网、路由表、NACL、IGW 等网络资源；开关打开后加 2 台 EC2、EC2 Instance Connect 端点与安全组 | 网络资源本身不收费；实例约 0.01 美元/小时 |
| 4-2 | `A02-02/labs/02-sg-lab` | test 6/6 | 15 to add | VPC、子网、web / app / db 安全组与规则、托管前缀列表；`enable_instances=true` 时加 2 台 EC2 与 EIC 端点 | 默认资源不收费；实例约 0.01 美元/小时 |
| 5-2 | `A02-03/labs/02-endpoint-lab` | test 4/4 | 19 to add | 无 NAT 的 VPC、2 个 VPC 终端节点、Lambda、S3 桶与对象、SSM 参数 | 接口终端节点约 0.01 美元/小时/AZ + 流量 |
| 6-3 | `A03-01/labs/02-sts-lab` | test 6/6 | 7 to add；`enable_boundary=true` 时 8 | IAM 角色与策略、S3 桶、桶策略与对象；必填 `operator_arn` | 几乎为 0 |
| 7-3 | `A03-02/labs/03-oidc-kms-secret` | test 7/7 | 7 to add（秘密值显示为 write-only） | GitHub OIDC 提供商、IAM 角色、KMS 密钥与别名、Secrets Manager 秘密 | KMS 1 美元/月 + 秘密 0.40 美元/月（按小时折算） |
| 8-2 | `A04-01/labs/02-alarms` | test 5/5 | 4 to add | 3 条指标告警、1 条复合告警 | 免费额度内通常为 0 |
| 9-3 | `A04-02/labs/03-terraform` | test 8/8 | 15 to add；`enable_alarm_path=true` 时 18 | 事件总线、规则与目标、SQS 队列、日志组、指标过滤器、保存的查询；开关打开后加告警与告警事件规则 | 几乎为 0 |
| 10-3 | `A05-01/labs/03-terraform` | test 6/6 | 4 to add；`create_lab_instance=true` 时 15 | 默认：SSM 文档、只读自动化角色与策略；实例模式另建 VPC、子网、安全组、EC2 实例与实例配置文件 | 默认 0；实例模式约 0.01 美元/小时 |
| 11-4 | `A06-01/labs/04-terraform` | test 5/5 | Part A 4 to add；`enable_config=true` 时 11 | Part A：S3 桶（所有权、公共访问阻止、默认加密）；Part B：Config 记录器、传递通道、日志桶与 `S3_BUCKET_TAGGED` 规则；必填 `bucket_name` | Part A 近乎 0；Part B 一轮约 0.02 美元 |
| 12-3 | `A06-02/labs/04-terraform` | test 4/4 | 7 to add；`enable_guardduty=true` 时 9 | KMS 密钥与别名、SSE-KMS 数据桶与桶策略；开关打开后加 GuardDuty 检测器与 S3 保护；必填 `bucket_name` | KMS 1 美元/月起；GuardDuty 按量（有 30 天试用） |
| 13-3 | `A07-01/labs/03-terraform` | test 5/5 | 8 to add | DynamoDB 表、备份库、备份计划与资源选择、2 个 IAM 角色 | 几乎为 0 |
| 14-2 | `A08-01/labs/02-terraform` | test 4/4 | 9 to add | VPC、子网、IGW、路由表、安全组与规则、1 台 EC2；必填 `client_cidr`（/32） | 约 0.01 美元/小时 |
| 15-1 | `A09-01/labs/01-lifecycle` | unittest 5/5 | 本机真实 init / plan / apply 六个阶段 | 只有 `terraform_data` 与本地状态，不创建 AWS 资源 | 0 |
| 15-2 | `A09-01/labs/02-state-backend` | test 2/2 | 7 to add | S3 状态桶（版本控制、默认加密、生命周期、所有权、公共访问阻止、桶策略）；必填 `bucket_name` | 约 0 |
| 16-2 | `A09-02/labs/02-drift-import/compare` | validate | 对默认 VPC：`1 to import, 0 to add, 1 to change` | **不要 apply**：会把默认 VPC 导入状态并按配置修改它 | 0 |
| 16-2 | `A09-02/labs/02-drift-import/generate` | validate | `-generate-config-out` 生成配置后 plan 报 Missing required argument（演示局限） | 不用于 apply | 0 |
| 17-2 | `A10-01/labs/02-terraform` | test 6/6 | 默认 0 个资源；`enable_paid_lab=true` 时 23 to add | 仅开关打开时：TGW，以及各 spoke VPC 的子网、路由表、TGW 附件与 TGW 路由表 | 约 0.10 美元/小时 |
| 18-2 | `A10-02/labs/02-request` | test 6/6 | 不需要：没有 provider，也不需要凭证 | 不创建任何资源（只校验 AFT 账户请求） | 0 |
| 19-4 | `FIN-01/labs/04-terraform` | test 4/4 | 默认 No changes；`enable=true` 且填 `notify_email` 时 3 to add | 仅开关打开时：带保留期的日志组、成本分摊标签激活、预算 | 预算（无动作）与标签激活免费 |

“test n/n”= `terraform test` 的 run 数（另含 `fmt -check` 与 `validate`）；“validate”= 没有 tests 的根模块，只做
`fmt -check` 与 `validate`。

**会改动 AWS 的脚本**（V1.0 均未运行，只做了 `bash -n` 语法检查与 CLI 参数核对）：

| 实验 | 脚本 | 会做什么 |
|---|---|---|
| 2-3 | `A01-01/labs/02-lambda-reliability/probe.py` | 调用 2-2 部署的函数（`--simulate` 离线模式已运行） |
| 8-3 | `A04-01/labs/02-alarms/publish.sh` | 上报自定义指标 |
| 9-4 | `A04-02/labs/03-terraform/scripts/` | 写日志、发事件、收消息 |
| 10-4 | `A05-01/labs/03-terraform/scripts/` | 实例模式下的故障注入与取证（其中只读的 `after-destroy.sh` 已运行） |
| 11-5 | `A06-01/labs/04-terraform/scripts/drift.sh` | 修改桶标签（同目录只读的 `preflight.sh` 已运行） |
| 12-3 | `A06-02/labs/04-terraform/scripts/` | 上传对象、生成样例 Finding |
| 13-3 | `A07-01/labs/03-terraform/scripts/` | 写表、备份、恢复（同目录只读的 `preflight.sh` 已运行） |
| 14-2 | `A08-01/labs/02-terraform/scripts/inject.sh` | 删除一条安全组规则 |

**已对实验账户实际运行的只读 / 计算型调用**（不改动资源、不收费）：1-1 预检；4-1 sgaudit；5-1 layers 探针；
6-1、6-2、7-1、10-2、11-3、12-2、15-2、16-3 的 IAM 策略模拟器与 Access Analyzer `validate-policy`；
9-2 EventBridge `test-event-pattern`；11-1 CloudTrail 事件历史；第 12 讲 posture 盘点；第 14 讲事件计数；
第 17 讲 Resolver / TGW 盘点；18-3 治理现状盘点；19-2 Price List 单价与 19-3 跨区域残留盘点；以及上表中的只读 plan。

## 验证状态（V1.0，2026-11-18）

| 检查 | 结果 |
|---|---|
| Python 单元测试（22 个实验目录） | 119 / 119 通过 |
| Terraform `fmt -check` / `validate` / `test`（18 个带 tests 的实验，全部 mock provider） | 18 / 18 通过，共 95 个 run |
| Terraform `fmt -check` / `validate`（5 个没有 tests 的根模块） | 5 / 5 通过 |
| GitHub Actions CI | 每次推送离线运行上面三项与 ZIP 校验；不连接 AWS、不使用任何凭证 |
| 只读 Plan | 18 个根模块对实验账户做过只读 plan（见上表）；1-3、1-4、2-4 因前提资源不存在、1-5 只做了 validate，共 4 个未执行；18-2 不需要 |
| 实际 Apply | V1.0：**没有对 AWS 执行任何 apply，没有创建资源**（唯一的真实 apply 是 15-1 在本机运行的 `terraform_data`）；V1.1：第 02 讲 2-2 / 2-3 已真实 apply 并销毁（10 added → 10 destroyed，残留 0），其余见 V1.1_PROGRESS.md |
| PDF 与源稿是否同步 | 19 个 PDF 均晚于各自的源稿、机制图、截图与构建工具 |
| ZIP 一致性 | PDF 合集与 `dist/pdf/`、源稿 ZIP 与 `textbook/` 源稿逐字节一致 |
| 截图 | 正文引用 53 张，全部存在且已脱敏；另有 3 张备用截图未在正文使用 |
| 敏感信息 | 源稿、PDF 文字层、截图 OCR 均未发现真实账户号、别名、邮箱、用户名；无 Terraform 状态与凭证文件 |

书中标为“本书实测输出”的内容，都来自只读 API、免费的计算型 API（IAM 策略模拟器、Access Analyzer、
EventBridge TestEventPattern、Price List）、本地运行或只读 `terraform plan`。截图中的账户号统一替换为
AWS 文档示例值 `111122223333`。

已知限制：有 3 处控制台页面没有采集到可用的截图（Config 规则搜索、Resolver 规则列表、安全组事件列表），
正文改用同一时间的只读命令输出。真实 apply / destroy 的实测、会改动 AWS 的脚本，以及这 3 处截图留给 V1.1
（见 [textbook/PROGRESS.md](textbook/PROGRESS.md)）。

## 许可

[Apache License 2.0](LICENSE)
