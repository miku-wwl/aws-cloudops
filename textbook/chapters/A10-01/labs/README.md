# 第 17 讲实验：TGW、VPN 与企业 DNS

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-18） |
|---|---|---|---|---|
| 17-1 往返推理模型 | `01-hybrid/` | 否（本地 Python，不发包、不调用 AWS） | 0 | 12 个场景输出见 `run-output.txt`；unittest 8/8 |
| 17-2 两张 TGW 表 | `02-terraform/` | 默认否；`enable_paid_lab=true` 时**是** | test/plan 0；apply 约 0.10 美元/小时 | `terraform test` 6/6；真实只读 plan：默认 0 个资源（`plan-default-2026-11-18.txt`），开启后 `Plan: 23 to add`（`plan-paid-2026-11-18.txt`） |

```bash
cd 01-hybrid && python hybrid.py scenarios.json && python hybrid.py scenarios.json S7 --trace && python -m unittest -v
cd ../02-terraform && terraform init && terraform test && terraform plan
terraform plan -var enable_paid_lab=true -out=paid.tfplan      # 审查：2 VPC、1 TGW、2 张 TGW 表、2 个附件、交叉传播
terraform apply paid.tfplan                                     # 约 0.10 美元/小时
aws ec2 search-transit-gateway-routes --transit-gateway-route-table-id <app 表 ID> --filters Name=type,Values=static,propagated
terraform destroy -var enable_paid_lab=true                     # 结束后确认附件已删除
```

停止条件：不是隔离的实验账户、plan 中出现非本实验的资源、或者任何变更可能影响现有 VPN / Direct Connect 时，立即停止。本实验不创建 EC2、VPN、Direct Connect 与 Resolver 端点；真实的 VPN 与 DX 需要对端设备或运营商交付，只做设计验证。
