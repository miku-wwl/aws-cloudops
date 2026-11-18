# 第 15 讲实验：Terraform 计划、状态与模块

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-18） |
|---|---|---|---|---|
| 15-1 生命周期六阶段 | `01-lifecycle/` | 否（`terraform_data`，本地状态） | 0 | 本机 Terraform 1.15.5 真实运行，输出 `run-output.txt`；真实计划 JSON 存于 `fixtures/`；unittest 5/5 |
| 15-2 状态桶引导 + 最小权限 | `02-state-backend/` | **是**（apply 时建桶） | 约 0 | `terraform test` 2/2；真实只读 plan：7 to add；访问策略 8 例与 IAM 模拟器一致（`statesim-2026-11-18.txt`）；Access Analyzer 无发现 |

```bash
cd 01-lifecycle && ./run.sh && python -m unittest          # 会在 work/ 下生成本地状态，可随时删除
cd ../02-state-backend && terraform init && terraform test && ./statesim.sh
terraform apply -var bucket_name=a15-<后缀>                   # 之后把 output.backend_block 贴进其他工程
```
