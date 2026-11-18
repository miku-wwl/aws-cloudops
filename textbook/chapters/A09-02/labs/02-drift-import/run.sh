#!/usr/bin/env bash
# 第 16 讲实验 16-2：只读 plan，观察“代码 ≠ 真实”与配置生成的局限。
#   bash run.sh
# 只执行 terraform plan：不导入、不 apply、不修改账户。
# 警告：不要在 compare/ 中执行 apply——它会真的把默认 VPC 的 enable_dns_hostnames 改成 false。
set -euo pipefail
cd "$(dirname "$0")"
VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text | tr -d '\r')
[ "$VPC_ID" != "None" ] || { echo "该区域没有默认 VPC，请用 -var vpc_id=<任一 VPC> 手动指定"; exit 1; }
echo "== 默认 VPC：$VPC_ID"

echo "== ① compare/：代码写 false，真实是 true"
( cd compare && terraform init -input=false -no-color >/dev/null \
  && terraform plan -input=false -no-color -var "vpc_id=$VPC_ID" | sed -E 's/[0-9]{12}/111122223333/g' )

echo "== ② generate/：从真实对象反推 HCL（预期 plan 报错，生成的文件需要人工整理）"
( cd generate && terraform init -input=false -no-color >/dev/null && rm -f generated.tf \
  && { terraform plan -input=false -no-color -var "vpc_id=$VPC_ID" -generate-config-out=generated.tf || true; } \
  && cat generated.tf )
