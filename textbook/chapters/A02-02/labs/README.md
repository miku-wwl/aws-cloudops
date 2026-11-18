# 第 04 讲实验：Security Group

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-17） |
|---|---|---|---|---|
| 4-1 sgaudit 审计 / 有效权限 | `01-sgaudit/` | 否（只读） | 0 | `python -m unittest`：5 个测试通过；已对实验账户 us-east-1 运行 |
| 4-2 安全组链 + 8080 对照实验 | `02-sg-lab/` | **是**（默认 15 个资源，不含实例） | SG/前缀列表/VPC 不收费；可选实例约 0.01 美元/小时 | `fmt`/`validate`；`terraform test` 6/6；真实 `plan`：15 to add；未 apply |

```bash
# 4-1（只读）
aws ec2 describe-security-groups --output json > sgs.json
cd 01-sgaudit && python -m unittest && python sgaudit.py audit --file ../sgs.json
python sgaudit.py allow --file fixtures/three-tier.json --sg sg-extra --sg sg-app --port 8080 --source-sg sg-web

# 4-2
cd ../02-sg-lab
terraform init && terraform test && terraform plan
terraform apply -var enable_instances=true                     # 可选：两台 t4g.nano + EIC 端点
aws ec2-instance-connect ssh --instance-id <client-id> --os-user ec2-user --connection-type eice
curl --connect-timeout 3 http://10.40.1.20:8080/health        # allow_8080=false：预期超时
terraform apply -var enable_instances=true -var allow_8080=true  # 预期返回 ok
terraform destroy
```

注意：`aws ec2 describe-security-groups` 的输出含有账户 ID，分享或提交前请先脱敏。
