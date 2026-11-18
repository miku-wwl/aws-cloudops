#!/usr/bin/env bash
# 第 12 讲实验 12-5 ①：上传一个“不带任何加密参数”的对象，再用 API 逐层核对（全部是真实 API 读取）。
# 用法（apply 之后）：./scripts/verify.sh [region]
set -euo pipefail
cd "$(dirname "$0")/.."
REGION="${1:-us-east-1}"; export AWS_PAGER=""
B="$(terraform output -raw bucket_name)"; K="$(terraform output -raw kms_key_arn)"
TMP="$(mktemp)"; echo "training object $(date -u +%FT%TZ)" > "$TMP"
aws s3api put-object --region "$REGION" --bucket "$B" --key lab/sample.txt --body "$TMP" --query '[ServerSideEncryption,SSEKMSKeyId,BucketKeyEnabled]' --output text
rm -f "$TMP"
echo "== 对象的实际加密（默认加密生效了吗？）"
aws s3api head-object --region "$REGION" --bucket "$B" --key lab/sample.txt --query '[ServerSideEncryption,SSEKMSKeyId,BucketKeyEnabled]' --output text
echo "   期望密钥：$K"
echo "== 公共访问阻止（4 个 True）";   aws s3api get-public-access-block --region "$REGION" --bucket "$B" --query 'PublicAccessBlockConfiguration' --output text
echo "== 默认加密与被阻止的类型";     aws s3api get-bucket-encryption --region "$REGION" --bucket "$B" --output json --query 'ServerSideEncryptionConfiguration.Rules[0]'
echo "== 对象所有权";                 aws s3api get-bucket-ownership-controls --region "$REGION" --bucket "$B" --query 'OwnershipControls.Rules[0].ObjectOwnership' --output text
echo "== 桶策略的 Sid";               aws s3api get-bucket-policy --region "$REGION" --bucket "$B" --query Policy --output text | python -c "import json,sys;print([s['Sid'] for s in json.load(sys.stdin)['Statement']])"
echo "== 策略的公开性评估（只评估桶策略本身）"; aws s3api get-bucket-policy-status --region "$REGION" --bucket "$B" --query 'PolicyStatus.IsPublic' --output text
