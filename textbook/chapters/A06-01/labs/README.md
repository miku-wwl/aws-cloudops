# 第 11 讲实验：CloudTrail × AWS Config

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-18） |
|---|---|---|---|---|
| 11-1 事件历史查询 | `02-ctquery/` | 否（LookupEvents 只读） | 0 | 已对实验账户真实运行（TestEventPattern、SimulateCustomPolicy、PutBucketTagging）；脱敏 unittest 3/3 |
| 11-2 标签 API 与规则语义 | `01-tagrule/` | 否 | 0 | unittest 7/7；事故时间线输出见教材 |
| 11-3 保护 Owner 的护栏 | `03-guardrail/` | 否（模拟器只做计算） | 0 | 6 个判定与 `iam simulate-custom-policy` 0 差异；Access Analyzer 按 IAM 与 SCP 两种类型校验均无发现 |
| 11-4 Terraform | `04-terraform/` | **是**（apply 时） | Part A 近乎 0；Part B 一轮约 0.02 美元 | `fmt`/`validate`；`terraform test` 5/5；真实只读 plan：Part A 4、Part B 11 to add；未 apply |
| 11-5 取证脚本 | `04-terraform/scripts/` | `drift.sh` 会改标签 | 同上 | `bash -n` 通过；`preflight.sh`（只读）已在实验账户运行 |

```bash
cd 02-ctquery && python -m unittest && python ctquery.py --name PutBucketTagging --hours 24
cd ../01-tagrule && python -m unittest && python s3tagged.py && python s3tagged.py --abac
cd ../03-guardrail && python -m unittest && python gsim.py            # --live 重新调用模拟器
cd ../04-terraform && terraform init && terraform test && ./scripts/preflight.sh
B=a11-<后缀>
terraform apply -var bucket_name=$B -var enable_config=true -var config_bucket_name=$B-cfg
./scripts/investigate.sh && ./scripts/drift.sh && sleep 600 && ./scripts/investigate.sh
terraform apply -var bucket_name=$B -var enable_config=true -var config_bucket_name=$B-cfg   # 恢复
terraform destroy -var bucket_name=$B -var enable_config=true -var config_bucket_name=$B-cfg
```

注意：一个账户的一个区域只能有一个客户托管配置记录器；`preflight.sh` 发现已有记录器时，只部署规则，不要接管别人的记录器。S3_BUCKET_TAGGED 在部分区域不可用（官方列出 Asia Pacific (New Zealand) 等）。
