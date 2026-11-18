# 第 13 讲实验：备份、恢复与灾备

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-18） |
|---|---|---|---|---|
| 13-1 RPO / RTO 计算 | `01-recovery-math/recovery.py` | 否 | 0 | 输出见教材 |
| 13-2 规范化哈希 | `01-recovery-math/canon.py` | 否 | 0 | 样例文件验证；unittest 6/6 |
| 13-3 Terraform | `03-terraform/` | **是**（apply 时） | 几乎为 0 | `fmt`/`validate`；`terraform test` 5/5；真实只读 plan：8 to add；未 apply |
| 13-3 脚本 | `03-terraform/scripts/` | **是**（写表、备份、恢复） | 几乎为 0 | `bash -n` 通过；`preflight.sh`（只读）已运行，输出 `preflight-2026-11-18.txt` |

```bash
cd 01-recovery-math && python -m unittest && python recovery.py timeline && python recovery.py strategies
python canon.py sample-baseline.json sample-restored.json
cd ../03-terraform && terraform init && terraform test && ./scripts/preflight.sh && terraform apply
./scripts/seed.sh && ./scripts/backup.sh && ./scripts/change-and-restore.sh && ./scripts/verify.sh
./scripts/inventory.sh
aws dynamodb delete-table --table-name "$(cat state/restored-table.txt)" && terraform destroy
```

注意：恢复出的新表不归 Terraform 管理，需手动删除；备份库 `force_destroy = true` 会在 destroy 时删除恢复点（不可逆，仅限实验）。
