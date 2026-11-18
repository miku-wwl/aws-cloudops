# 第 05 讲实验：DNS 与 VPC 终端节点

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-17） |
|---|---|---|---|---|
| 5-1 layers 逐层探测 | `01-layers/` | 否（一个只读请求） | 0 | 已对 ssm / s3 公网端点实测（输出见教材） |
| 5-2 无 NAT 终端节点实验 | `02-endpoint-lab/` | **是**（19 个资源） | 接口终端节点约 0.01 美元/小时/AZ + 流量 | `fmt`/`validate`；`terraform test` 4/4；真实 `plan`：19 to add；未 apply |
| 5-3 故障与修复 | 同上 | **是** | 同上 | 给出预期现象 |

```bash
# 5-1（本地）
python 01-layers/layers.py ssm.us-east-1.amazonaws.com --api ssm

# 5-2 / 5-3
cd 02-endpoint-lab
terraform init && terraform test && terraform apply            # 默认 allow_https=false（故障态）
for m in dns s3 ssm; do
  aws lambda invoke --function-name a05-endpoint-probe --cli-binary-format raw-in-base64-out \
    --payload "{\"mode\":\"$m\"}" out-$m.json && cat out-$m.json; echo
done
terraform apply -var allow_https=true                          # 只新增一条入站规则
aws lambda invoke --function-name a05-endpoint-probe --cli-binary-format raw-in-base64-out \
  --payload '{"mode":"ssm"}' out-ssm-after.json && cat out-ssm-after.json
terraform destroy
```

Lambda 的部署包直接引用 `../01-layers/layers.py`，因此两个目录要一起复制。
