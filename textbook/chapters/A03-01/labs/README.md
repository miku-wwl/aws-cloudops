# 第 06 讲实验：IAM 策略评估与 STS

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-17） |
|---|---|---|---|---|
| 6-1 iameval × AWS 模拟器 | `01-iameval/` | 否（`iam:SimulateCustomPolicy` 只读） | 0 | unittest 4/4；8 个场景、12 个判定与 AWS 模拟器 0 处不一致 |
| 6-2 Access Analyzer 校验 | `01-iameval/policies/` | 否（`validate-policy`） | 0 | 已实测：bad-fix 2 条发现，good-fix 无发现 |
| 6-3 角色、信任、精确授权 | `02-sts-lab/` | **是**（7～8 个资源） | 几乎为 0 | `fmt`/`validate`；`terraform test` 6/6；真实 `plan`：7 / 8 to add；未 apply |

```bash
# 6-1 / 6-2（只读）
cd 01-iameval
python -m unittest
MSYS_NO_PATHCONV=1 python iameval.py scenarios.json --aws        # Git Bash 下需关闭路径转换
aws accessanalyzer validate-policy --policy-type IDENTITY_POLICY --policy-document file://policies/bad-fix.json

# 6-3
cd ../02-sts-lab
terraform init && terraform test
terraform apply -var operator_arn=$(aws sts get-caller-identity --query Arn --output text)
./probe.sh $(terraform output -raw reader_role_arn) $(terraform output -raw lab_bucket)          # health ✓ report ✗
terraform apply -var operator_arn=... -var allow_report=true                                     # 两者 ✓
terraform apply -var operator_arn=... -var allow_report=true -var enable_boundary=true           # report 再次 ✗
./probe.sh <role> <bucket> session-logs-only.json                                                # 会话策略收窄
terraform destroy
```

Windows：`Test-A06Access.ps1` 与 `probe.sh` 等价（文件为 UTF-8 BOM，兼容 Windows PowerShell 5.1）。
