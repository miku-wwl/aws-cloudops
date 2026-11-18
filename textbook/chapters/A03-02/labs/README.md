# 第 07 讲实验：联邦身份、KMS 与 Secrets Manager

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-17） |
|---|---|---|---|---|
| 7-1 令牌 × 信任策略矩阵 | `01-oidc-trust/` | 否（`validate-policy` 免费） | 0 | unittest 4/4；Access Analyzer 实测发现见教材 |
| 7-2 本地信封加密 | `02-envelope/` | 否 | 0 | unittest 4/4；演示输出见教材 |
| 7-3 OIDC + KMS + 秘密 | `03-oidc-kms-secret/` | **是**（7 个资源） | KMS 1 美元/月 + 秘密 0.40 美元/月（按小时折算） | `fmt`/`validate`；`terraform test` 7/7；真实 `plan`：7 to add（秘密值显示为 write-only）；未 apply |
| 7-4 GitHub Actions 探针 | `03-oidc-kms-secret/.github/workflows/` | 只读调用 | 可忽略 | YAML 已校验；未在 GitHub 运行 |

```bash
cd 01-oidc-trust && python -m unittest && MSYS_NO_PATHCONV=1 python oidc_trust.py --aws
cd ../02-envelope && python -m unittest && python envelope.py

cd ../03-oidc-kms-secret            # 需要 Terraform ≥ 1.11（只写参数）
terraform init && terraform test
# 新仓库（2026-07-15 之后创建）要用含数字 ID 的 sub：
#   gh api repos/<owner>/<repo> --jq '.owner.id, .id'
terraform apply -var 'github_sub_prefix=repo:<owner>@<ownerId>/<repo>@<repoId>'
# 复制工作流到仓库 .github/workflows/，设置仓库变量 A07_ROLE_ARN、A07_SECRET_ARN 后手动运行
terraform apply -var 'github_sub_prefix=…' -var allow_kms_decrypt=true    # 修复
terraform destroy      # KMS 密钥进入 7 天待删除（不计费），秘密进入 7 天恢复期
```
