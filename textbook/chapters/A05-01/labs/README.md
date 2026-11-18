# 第 10 讲实验：Systems Manager 无 SSH 运维

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-18） |
|---|---|---|---|---|
| 10-1 四层推理模型 | `01-ssmdiag/` | 否 | 0 | 12 个场景；unittest 8/8 |
| 10-2 操作者最小权限 | `02-operator-iam/` | 否（模拟器只做计算） | 0 | 10 个判定与真实 `iam simulate-custom-policy` 0 差异；Access Analyzer `validate-policy` 无发现；unittest 2/2 |
| 10-3 Terraform | `03-terraform/` | **是**（apply 时） | 默认模式 0；实例模式约 0.01 美元/小时 | `fmt`/`validate`；`terraform test` 6/6；真实只读 `plan`：默认 4 to add，实例模式 15 to add；未 apply |
| 10-4 故障注入与取证 | `03-terraform/scripts/` | **是**（实例模式） | 同上 | `bash -n` 通过；CLI 参数已核对；`after-destroy.sh`（只读）已在实验账户运行，五项为空 |

```bash
# 10-1、10-2：零费用
cd 01-ssmdiag && python -m unittest && python ssmdiag.py scenarios.json
cd ../02-operator-iam && python -m unittest && python opsim.py           # 离线对照录制结果
python opsim.py --live                                                    # 需要 iam:SimulateCustomPolicy

# 10-3：只读验证
cd ../03-terraform && terraform init && terraform test && terraform plan && terraform plan -var create_lab_instance=true

# 10-4：独立实验账户（实例模式按小时计费）
terraform apply -var create_lab_instance=true
./scripts/status.sh && ./scripts/diag.sh && ./scripts/inventory.sh
./scripts/fault.sh off && sleep 300 && ./scripts/status.sh && ./scripts/diag.sh && ./scripts/inventory.sh
./scripts/fault.sh on  && sleep 300 && ./scripts/status.sh && ./scripts/diag.sh
terraform destroy -var create_lab_instance=true && ./scripts/after-destroy.sh
```

注意：

- 实例为 t4g.nano（arm64），AMI 取自公共参数 `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64`；`instance_type` 只接受 Graviton 机型。
- `operator-policy.json` 中的账户 ID 111122223333 是示例值，模拟时无需替换；真正使用前替换为实际账户与区域。
- 故障注入后要重启实例：安全组有状态，删除规则不会切断已跟踪的长连接。
- 只在独立实验账户、本章创建的安全组上做故障注入。
