#!/usr/bin/env bash
# 第 18 讲实验 18-3：只读盘点“这个账户在多账户治理中处于什么位置”。全部为只读 API，不收费。
#   bash inventory.sh | tee inventory-$(date +%F).txt
set -uo pipefail
R=${AWS_REGION:-us-east-1}
mask() { sed -E 's/[0-9]{12}/111122223333/g'; }

echo "== 组织"
aws organizations describe-organization --query 'Organization.[Id,FeatureSet,MasterAccountId]' --output text 2>&1 | mask

echo "== Control Tower 着陆区（$R）"
aws controltower list-landing-zones --region "$R" --query 'landingZones[].arn' --output text 2>&1 | mask
[ -z "$(aws controltower list-landing-zones --region "$R" --query 'landingZones[0].arn' --output text 2>/dev/null | grep -v None)" ] && echo "（无着陆区）"

echo "== Control Tower 基线目录（可以在 OU / 账户上启用的基线）"
aws controltower list-baselines --region "$R" --query 'baselines[].name' --output text 2>&1 | tr '\t' '\n' | sort | paste -sd ' ' -

echo "== 已在 OU 上启用的基线"
aws controltower list-enabled-baselines --region "$R" --query 'length(enabledBaselines)' --output text 2>&1 | mask

echo "== Service Catalog 组合数（Account Factory 依赖它）"
aws servicecatalog list-portfolios --region "$R" --query 'length(PortfolioDetails)' --output text 2>&1
