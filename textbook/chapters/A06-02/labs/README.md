# 第 12 讲实验：安全检测与数据保护

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-18） |
|---|---|---|---|---|
| 12-1 两道门模型 | `01-twogates/` | 否 | 0 | 10 个场景；unittest 5/5 |
| 账户现状盘点 | `02-posture/` | 否（只读） | 0 | 已在实验账户运行，输出见 `posture-2026-11-18.txt`（账户号已替换） |
| 12-2 策略模拟 | `03-policysim/` | 否（模拟器只做计算） | 0 | 已运行：TLS 桶策略 3 例结果正确；记录了模拟器对 KMS 密钥策略的局限；桶策略经 Access Analyzer 校验无发现 |
| 12-3 Terraform 数据桶 | `04-terraform/` | **是**（apply 时） | KMS 1 美元/月起 + 按量；GuardDuty 可选 | `fmt`/`validate`；`terraform test` 4/4；真实只读 plan：7 to add（开 GuardDuty 9）；未 apply |
| 验证脚本 | `04-terraform/scripts/` | **是**（上传对象、样例 Finding） | 极少 | `bash -n` 通过；未运行 |

```bash
cd 01-twogates && python -m unittest && python twogates.py scenarios.json
cd ../02-posture && ./posture.sh
cd ../03-policysim && ./policysim.sh
cd ../04-terraform && terraform init && terraform test && terraform plan -var bucket_name=a12-<后缀>
terraform apply -var bucket_name=a12-<后缀> -var 'key_user_arns=["arn:aws:iam::<账户>:role/<角色>"]'
./scripts/verify.sh && ./scripts/negative-tls.sh
aws s3 rm s3://a12-<后缀> --recursive && terraform destroy -var bucket_name=a12-<后缀>
```

注意：KMS 密钥 destroy 后进入 7 天待删除期（不收月费，但不可用）；账户中已有 GuardDuty 检测器时不要设置 `enable_guardduty=true`（一个区域只能有一个检测器）。
