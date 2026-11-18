# AWS CloudOps 工程教材 · 2026 修订版

面向云运维 / 平台 / SRE 工程师的 19 讲 AWS CloudOps 教材。每一讲都从一个真实的排障问题出发，按
**情境 → 机制图 → 分步例题 → 实验 → 故障卡 → 练习与解析** 组织（版式参照《高中物理·加速度》样章），
所有结论都附有可复现的证据：本地模型与单元测试、Terraform 测试与只读 plan、免费的只读 / 计算型 AWS API，
以及已脱敏的真实控制台截图。内容按 2026 年 11 月的 AWS 官方文档与控制台核对。

## 下载

| 内容 | 位置 | 大小 |
|---|---|---|
| 19 讲 PDF 合集 | [textbook/dist/AWS-CloudOps-19讲-PDF合集-2026-11.zip](<textbook/dist/AWS-CloudOps-19讲-PDF合集-2026-11.zip>) | 36 MB |
| 全部可编辑源稿与实验工程 | [textbook/dist/AWS-CloudOps-19讲-源稿与实验工程-2026-11.zip](<textbook/dist/AWS-CloudOps-19讲-源稿与实验工程-2026-11.zip>) | 5 MB |
| 单讲 PDF | [textbook/dist/pdf/](textbook/dist/pdf) | 19 个，共 242 页 |

在 GitHub 上打开 ZIP 文件后，点击 “Download raw file” 即可下载。两个 ZIP 由 `textbook/tools/package.py` 生成，
并与 `dist/pdf/` 和源稿逐字节校验一致。

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
├── archive/original-pdfs/        重写前的 19 讲原版讲义（只读存档）
└── textbook/
    ├── README.md                 源稿约定、截图与脱敏方法
    ├── PROGRESS.md               逐讲完成记录与 2026 年核对过的新事实
    ├── tools/                    build.py（Markdown → HTML → PDF → QA）、style.css、figlib.py（机制图）、
    │                             shot.py（截图规范化）、pages.py（逐页审阅）、package.py（打包与校验）、
    │                             test_all.sh（全部离线测试）、console_prep.js（截图前页面内脱敏模板）
    ├── chapters/<编号>/           共 19 个
    │   ├── chapter.md            正文源稿（Pandoc Markdown）
    │   ├── figures/              机制图源码 figs.py 与生成的 SVG（共 81 张）
    │   ├── screenshots/          真实控制台截图（正文使用 53 张，已脱敏）
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
```

## 实验怎样使用

- 每讲的 `labs/README.md` 写明每个实验**会不会改动 AWS、费用多少、验证状态**和运行命令。
- **Python 模型**（路由、IAM 评估、告警、事件匹配、账单分类……）完全离线：`python -m unittest -v`。
- **Terraform 实验**都带 `tests/*.tftest.hcl`（mock provider，不连 AWS）：`terraform init && terraform test`。
  默认变量下 `terraform plan` 是零资源；需要真实资源的实验有显式开关（如 `enable_paid_lab = true`），
  README 中给出费用估算与销毁、复核步骤。请只在隔离的实验账户中 apply，结束后立即 destroy。
- 一次运行全部离线测试：`cd textbook && bash tools/test_all.sh`
  （可设 `PLUGIN_DIR=<本地 provider 目录>` 离线安装 provider；结束后可删除各实验下的 `.terraform/`）。

## 验证状态（2026-11-18）

| 检查 | 结果 |
|---|---|
| Python 单元测试（22 个实验目录） | 119 / 119 通过 |
| Terraform `fmt -check` / `validate` / `test`（18 个实验） | 18 / 18 通过，共 95 个 run |
| PDF 与源稿是否同步 | 19 个 PDF 均晚于各自的源稿、机制图与构建工具 |
| ZIP 一致性 | PDF 合集与 `dist/pdf/`、源稿 ZIP 与 `textbook/` 源稿逐字节一致 |
| 敏感信息 | 源稿、PDF 文字层、截图 OCR 均未发现真实账户号、别名、邮箱、用户名；无 Terraform 状态与凭证文件 |

书中标为“本书实测输出”的内容，都来自只读 API、免费的计算型 API（IAM 策略模拟器、Access Analyzer、
EventBridge TestEventPattern、Price List）、本地运行或只读 `terraform plan`。编写过程中**没有在 AWS 账户中创建
任何资源**；会产生费用的云上实验保留为可选步骤。截图中的账户号统一替换为 AWS 文档示例值 `111122223333`。

已知限制：有 3 处控制台页面没有采集到可用的截图（Config 规则搜索、Resolver 规则列表、安全组事件列表），
正文改用同一时间的只读命令输出。

## 许可

[Apache License 2.0](LICENSE)
