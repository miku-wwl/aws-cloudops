# 第 19 讲实验：FinOps 与成本回收

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-18） |
|---|---|---|---|---|
| 19-1 账单行分类器 | `01-audit/` | 否（本地 Python） | 0 | 6 个案例输出见 `run-output.txt`；unittest 6/6；金额用真实单价计算 |
| 19-2 真实单价估算 | `02-estimate/` | 否（Price List API 只读、免费） | 0 | `prices.json` 为 2026-11-18 us-east-1 实时单价；合计 0.1656 美元（销毁后 0.0589） |
| 19-3 跨区域残留盘点 | `03-inventory/` | 否（只读 API） | 0 | 3 个区域、9 类资源 + S3；发现 us-west-2 一个“永不过期”的孤立 Lambda 日志组 |
| 19-4 归属、保留期与预算 | `04-terraform/` | 默认否；`enable=true` 时**是** | 预算（无动作）与标签激活免费 | `terraform test` 4/4；真实只读 plan：默认 No changes，开启后 `Plan: 3 to add` |

```bash
cd 01-audit && python audit.py cases/*.json && python -m unittest -v
cd ../02-estimate && python fetch_prices.py > prices.json && python estimate.py prices.json scenario.json
cd ../03-inventory && REGIONS="us-east-1 us-west-2" bash inventory.sh
cd ../04-terraform && terraform init && terraform test && terraform plan
```

清理原则：只读盘点 → 确认归属与保留要求 → 获批后处置 → 等旧用量入账后复核。生产或共享账户、归属不明、有合规保留要求时，只做只读观察。
