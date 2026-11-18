# 第 14 讲实验：事故响应与根因分析

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-18） |
|---|---|---|---|---|
| 14-1 鉴别诊断与时间窗 | `01-ir/` | 否 | 0 | unittest 4/4；输出见教材 |
| 14-2 Web 入口 | `02-terraform/` | **是**（apply 时） | 约 0.01 美元/小时 | `fmt`/`validate`；`terraform test` 4/4；真实只读 plan：9 to add；未 apply |
| 14-2 脚本 | `02-terraform/scripts/` | `inject.sh` 会删除一条规则 | 同上 | `bash -n` 通过；未运行 |

```bash
cd 01-ir && python -m unittest && python ir.py dx case.json && python ir.py window probes.jsonl --alert 2026-11-17T10:12:00Z
cd ../02-terraform && terraform init && terraform test
export CLIENT_CIDR="$(curl -s https://checkip.amazonaws.com)/32"
terraform apply -var client_cidr=$CLIENT_CIDR
./scripts/probe.sh 5 60 && ./scripts/inject.sh && ./scripts/probe.sh 5 60 && ./scripts/investigate.sh
terraform apply -var client_cidr=$CLIENT_CIDR && ./scripts/probe.sh 5 60
python ../01-ir/ir.py window probes.jsonl
terraform destroy -var client_cidr=$CLIENT_CIDR
```

复盘请填写 `02-terraform/scripts/rca-template.md`。
