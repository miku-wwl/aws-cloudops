# 第 01 讲实验：Landing Zone 与 Control Tower 4.0

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-17） |
|---|---|---|---|---|
| 1-1 只读预检 | `01-preflight/` | 否（只读 API） | 0 | 已在实验账户执行，输出见教材 |
| 1-2 manifest 本地测试 | `02-landing-zone/tests/` | 否（mock provider） | 0 | `terraform test`：5 passed |
| 1-3 Landing Zone IaC | `02-landing-zone/` | **是**（apply 会创建 LZ 与服务角色） | 持续产生 CloudTrail/Config/S3 费用 | `fmt`、`validate` 通过；未 apply |
| 1-4 OU 治理 | `03-ou-governance/` | **是** | 依控制而定 | `fmt`、`validate` 通过；未 apply |
| 1-5 漂移告警 | `04-drift-alerts/` | **是**（规则 + SNS） | 近似 0 | `fmt`、`validate` 通过；未 apply |
| 1-6 落地验收 | `05-verify/` | 否（只读 API） | 0 | 需要已部署的 Landing Zone |

## 快速开始（零费用部分）

```bash
cd 01-preflight && bash preflight.sh us-east-1          # 或 pwsh ./preflight.ps1
cd ../02-landing-zone && terraform init -backend=false && terraform test
```

## 需要真实组织的部分

1. 在**专用沙箱组织**的管理账户中执行，不要在已有生产组织里试验。
2. 先按教材第七部分准备组织、集成账户（同一个根级 OU）与三个服务角色的前置条件。
3. `02-landing-zone`：复制 `terraform.tfvars.example` 为 `terraform.tfvars` 并填入真实账户 ID，`terraform plan` 审阅后再 apply（部署约 30–60 分钟）。
4. 部署完成后用 `aws controltower list-enabled-baselines` 查到 IdentityCenterBaseline 的 enabledbaseline ARN，填入 `03-ou-governance` 的 `idc_baseline_arn`。
5. `05-verify/verify.sh <home-region> <ou-arn> [account-id]` 收集验收证据。

## 清理

Landing Zone 带有 `prevent_destroy`，不能用一次 `terraform destroy` 删除；退役请按 AWS 文档的 decommission 流程执行。`04-drift-alerts` 可以直接 `terraform destroy`。
