# 第 02 讲实验：Well-Architected 与可靠性

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-17） |
|---|---|---|---|---|
| 2-1 SLO 计算器 | `01-slo-calculator/` | 否 | 0 | `python -m unittest`：8 个测试通过 |
| 2-2 可注入故障的负载 | `02-lambda-reliability/` | **是**（10 个资源） | Lambda 在免费额度内；告警约 2 美元/月按小时折算 | `fmt`/`validate` 通过；`terraform test` 6/6；对真实账户 `plan`：10 to add；**V1.1（2026-11-19）LIVE APPLY 10 added → DESTROYED 10 destroyed，残留 0**（`02-lambda-reliability/live-2026-11-19.txt`） |
| 2-3 故障注入与探针 | `02-lambda-reliability/probe.py` | 只调用函数 | 免费额度内 | `--simulate` 离线模式已运行；**V1.1 真实模式 LIVE VERIFIED：注入 fail_rate=0.2 后 39/200 失败、6 条告警 ALARM；RECOVERED：200/200 成功** |
| 2-4 FIS 实验模板 | `03-fis-experiment/` | **是** | 约 2 个 FIS 动作分钟 | `fmt`/`validate` 通过；未 apply |

## 运行顺序

```bash
# 2-1（本地）
cd 01-slo-calculator && python -m unittest && python slo.py table --slo 99.9

# 2-2（云上，专用实验账户）
cd ../02-lambda-reliability
terraform init && terraform test && terraform plan -out=base.tfplan && terraform apply base.tfplan

# 2-3
python probe.py --function-name ticket-query --count 200
terraform apply -var="fail_rate=0.2"
aws lambda wait function-updated --function-name ticket-query
python probe.py --function-name ticket-query --count 200
terraform plan -out=recover.tfplan && terraform apply recover.tfplan   # 恢复

# 2-4（可选）：先以 enable_fis_extension=true、fis_config_bucket=<桶名> 重新 apply 2-2
cd ../03-fis-experiment
terraform apply -var="function_arn=..." -var="stop_alarm_arn=..." -var="config_bucket=<桶名>"
aws fis start-experiment --experiment-template-id <id>

# 清理（倒序）
terraform destroy   # 03-fis-experiment，再 02-lambda-reliability
```

`probe.py` 真实模式需要 `boto3`；它关闭了 SDK 自动重试，以免限流被重试掩盖。
