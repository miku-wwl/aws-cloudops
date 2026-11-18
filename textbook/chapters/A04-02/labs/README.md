# 第 09 讲实验：Logs Insights × EventBridge

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-17） |
|---|---|---|---|---|
| 9-1 本地 Logs Insights 引擎 | `01-insights/` | 否 | 0 | unittest 14/14；`../queries/*.cwli` 6 条查询全部跑通，输出见教材 |
| 9-2 事件模式匹配器 | `02-patterns/` | 否（TestEventPattern 只做计算） | 0 | 20 个用例与真实 `aws events test-event-pattern` 0 差异；离线 unittest 4/4 |
| 9-3 Terraform 环境 | `03-terraform/` | **是**（apply 时创建 15 个资源，可选 18 个） | 资源本身几乎为 0 | `fmt`/`validate`；`terraform test` 8/8；真实只读 `plan`：15 to add（告警路径 18）；未 apply |
| 9-4 云上全链路 | `03-terraform/scripts/` | **是**（写日志、发事件、收消息） | 一轮 < 0.01 美元 | `bash -n` 语法检查通过；CLI 参数已核对；未运行 |

共享文件：

- `data/requests.jsonl`：16 条样本（基线 v1 ×4、金丝雀 v2 ×8（6 个 5xx，全在 /checkout）、回滚 v1 ×4）。
- `queries/*.cwli`：6 条 Logs Insights QL 查询。实验 9-1 用它们计算教材中的数字；实验 9-3 把它们部署为“保存的查询”。

```bash
# 9-1、9-2：本地，零费用
cd 01-insights && python -m unittest && python insights.py ../data/requests.jsonl --all ../queries
cd ../02-patterns && python -m unittest && python patterns.py          # 离线对照录制结果
python patterns.py --live                                               # 需要 AWS 凭证；只调用 TestEventPattern

# 9-3：只读验证
cd ../03-terraform && terraform init && terraform test && terraform plan

# 9-4：在独立实验账户中（会产生极少量费用）
terraform apply
./scripts/seed-logs.sh && ./scripts/query.sh ../queries/03-error-rate.cwli
./scripts/send-events.sh && ./scripts/receive.sh && ./scripts/receive.sh --delete
./scripts/check.sh
terraform destroy
```

注意：

- 日志组保留期为 1 天；`seed-logs.sh` 会把样本时间平移到“最近 4 分钟”，否则旧时间戳会被拒收（`tooOldLogEventEndIndex`）。
- 队列使用 SSE-SQS；不要改成 `alias/aws/sqs`（EventBridge 无法使用该 AWS 托管密钥）。
- `terraform test` 中的 mock provider 使用 `override_during = plan`，需要较新的 Terraform（本书用 1.15.5 验证）；配置本身要求 ≥ 1.9。
- 脚本在 Git Bash（Windows）与 AWS CloudShell 中均可运行；Git Bash 下临时文件路径会经 `cygpath -w` 转换后交给 `aws.exe`。
