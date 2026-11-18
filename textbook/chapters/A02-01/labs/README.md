# 第 03 讲实验：VPC 路由与 NACL

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-17） |
|---|---|---|---|---|
| 3-1 pathcheck 逐跳分析 | `01-pathcheck/` | 否 | 0 | `python -m unittest`：9 个测试通过；7 个场景 |
| 3-2 可注入故障的 VPC | `02-vpc-lab/` | **是**（默认 12 个网络资源） | 网络资源本身不收费 | `fmt`/`validate`；`terraform test` 6/6；真实 `plan`：12 / 28 to add；未 apply |
| 3-3 真实发包（可选） | `02-vpc-lab/`（`enable_instances=true`） | **是** | 约 0.01 美元/小时 | 仅给出预期现象 |
| 3-4 只读检查默认 VPC | 下方命令 | 否 | 0 | 输出已写入教材 |

```bash
# 3-1
cd 01-pathcheck && python -m unittest && python pathcheck.py scenarios/no-ephemeral-out.json

# 3-2 / 3-3
cd ../02-vpc-lab
terraform init && terraform test && terraform plan
terraform apply -var enable_instances=true                       # 可选计算阶段
aws ec2-instance-connect ssh --instance-id <client-id> --os-user ec2-user --connection-type eice
curl --connect-timeout 3 http://10.20.2.20:8080                  # 预期 A02_OK
terraform apply -var enable_instances=true -var block_app_port=true                         # 故障 1
terraform apply -var enable_instances=true -var nacl_mode=strict -var drop_ephemeral_out=true  # 故障 2
terraform destroy

# 3-4（只读）
aws ec2 describe-route-tables --filters Name=vpc-id,Values=<vpc-id> \
  --query 'RouteTables[].Routes[].[DestinationCidrBlock,GatewayId,State,Origin]' --output table
aws ec2 describe-network-acls --filters Name=vpc-id,Values=<vpc-id> \
  --query 'NetworkAcls[].Entries[].[Egress,RuleNumber,Protocol,CidrBlock,RuleAction]' --output table
aws ec2 describe-vpc-block-public-access-options
```
