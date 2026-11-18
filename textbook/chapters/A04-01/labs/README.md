# 第 08 讲实验：CloudWatch 指标与告警

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-17） |
|---|---|---|---|---|
| 8-1 alarmsim 模拟器 | `01-alarmsim/` | 否 | 0 | unittest 3/3；复现 AWS 文档判定表 40/40；时间线输出见教材 |
| 8-2 四条告警 | `02-alarms/` | **是**（4 条告警） | 免费额度内通常为 0 | `fmt`/`validate`；`terraform test` 5/5；真实 `plan`：4 to add；未 apply |
| 8-3 真实上报与观察 | `02-alarms/publish.sh`、`inspect.sh` | **是**（自定义指标） | 免费额度内通常为 0 | 脚本语法已检查；未运行 |

```bash
cd 01-alarmsim && python -m unittest && python alarmsim.py table && python alarmsim.py timeline
cd ../02-alarms && terraform init && terraform test && terraform apply
./publish.sh baseline && ./inspect.sh
./publish.sh fault && ./inspect.sh
./publish.sh recovery && sleep 600 && ./inspect.sh      # 停发后观察心跳告警
terraform destroy
```
