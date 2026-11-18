# 第 16 讲实验：远程状态、OIDC 与漂移

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-18） |
|---|---|---|---|---|
| 16-1 四道控制推理模型 | `01-pipeline/` | 否（本地 Python） | 0 | D1–D7、R1–R3 全部输出与正文一致；unittest 3/3 |
| 16-2 漂移与配置生成 | `02-drift-import/` | 否（只读 `terraform plan`，不导入、不 apply） | 0 | 对默认 VPC 的真实只读 plan：`Plan: 1 to import, 0 to add, 1 to change, 0 to destroy`（`compare/plan-2026-11-18.txt`，账户号已替换）；生成的配置含 `ipv6_netmask_length = 0`，plan 报 Missing required argument（`generate/generated-2026-11-18.tf.txt`） |
| 16-3 受保护的工作流与信任策略 | `03-workflow/` | 否（Access Analyzer `validate-policy` 只做校验） | 0 | 工作流 YAML 解析通过；三份信任策略校验结果见 `validate-2026-11-18.txt`：加 `ref` 条件后应用角色的 WARNING 消失 |

```bash
cd 01-pipeline && python pipeline.py scenarios.json && python -m unittest -v
cd ../02-drift-import && bash run.sh          # 需要 ec2:DescribeVpcs 等只读权限；不要在 compare/ 中 apply
cd ../03-workflow && bash validate.sh         # 需要 access-analyzer:ValidatePolicy
```

## 把工作流用到自己的仓库

1. 在 IAM 中创建 GitHub OIDC 身份提供商（`token.actions.githubusercontent.com`，受众 `sts.amazonaws.com`），以及计划角色与应用角色；把 `trust-*.json` 中的账户号、`example-org@1234/cloudops-lab@5678` 换成自己的所有者 / 仓库名与数字 ID（`gh api repos/<owner>/<repo> --jq '.owner.id, .id'`）。
2. 计划角色：只读 + 状态读 + 锁对象读写；应用角色：业务所需写权限 + 第 15 讲的状态访问策略。
3. 仓库 Settings → Environments → `production`：Required reviewers；Deployment branches 只允许 `main`。
4. 把 `PLAN_ROLE_ARN` / `APPLY_ROLE_ARN` 写成仓库变量（不是密钥：ARN 不是凭证），把 `.github/workflows/terraform.yml` 与第 15 讲的 `inspect_plan.py`（放到 `tools/`）复制进仓库。
5. 生产中把各个 `uses:` 固定到完整的提交 SHA。
