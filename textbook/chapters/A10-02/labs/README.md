# 第 18 讲实验：Control Tower、AFT 与 LZA

| 实验 | 目录 | 会不会改动 AWS | 费用 | 验证状态（2026-11-18） |
|---|---|---|---|---|
| 18-1 账户交付判定器 | `01-delivery/` | 否（本地 Python） | 0 | 10 个案例输出见 `run-output.txt`；unittest 6/6 |
| 18-2 AFT 请求合入前检查 | `02-request/` | 否（离线 terraform test，不需要 provider 与凭证） | 0 | `terraform test` 6/6 |
| 18-3 治理现状只读盘点 | `03-inventory/` | 否（只读 API） | 0 | `inventory-2026-11-18.txt`：账户不属于任何组织、无着陆区、基线目录 10 项 |

```bash
cd 01-delivery && python delivery.py cases.json && python delivery.py cases.json C5 -v && python -m unittest -v
cd ../02-request && terraform init && terraform test
cd ../03-inventory && bash inventory.sh
```

把 18-2 用到真实的 `aft-account-request` 仓库：在 CI 中把每个账户请求的输入复制成 `request` 变量（或直接把校验写进仓库内的包装模块），合入前运行 `terraform test`。注意：在已部署 AFT 的仓库里，合入并推送请求就会真实开户。

本讲不执行任何组织级部署（Control Tower、AFT、CfCT、LZA 都会长期修改多账户资源，且难以一次性清理）。控制台截图只浏览了 Control Tower 设置向导的前两步，没有点击 “Create Organization”。
