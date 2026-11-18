#!/usr/bin/env bash
# 第 11 讲实验 11-5 ⓪：启用 Config 之前的只读盘点。已有客户托管记录器 / 投递通道时，不要再建第二个。
# 用法：./scripts/preflight.sh [region]
set -uo pipefail
REGION="${1:-us-east-1}"; export AWS_PAGER=""
echo "== 配置记录器（客户托管 + 服务关联）"; aws configservice describe-configuration-recorders --region "$REGION" \
  --query 'ConfigurationRecorders[].[name,recordingGroup.allSupported,servicePrincipal]' --output text
echo "== 投递通道"; aws configservice describe-delivery-channels --region "$REGION" --query 'DeliveryChannels[].name' --output text
echo "== 现有规则数"; aws configservice describe-config-rules --region "$REGION" --query 'length(ConfigRules)'
echo "== Config 服务关联角色"; aws iam get-role --role-name AWSServiceRoleForConfig --query 'Role.Path' --output text 2>&1 | tail -1
echo "== 跟踪（trail）"; aws cloudtrail describe-trails --region "$REGION" --query 'trailList[].Name' --output text
echo "== 本区域现有桶数（Config 只记 S3 类型时，会记录全部这些桶）"
aws s3api list-buckets --query 'length(Buckets)' --output text
