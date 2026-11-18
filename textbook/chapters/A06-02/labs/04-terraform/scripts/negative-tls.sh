#!/usr/bin/env bash
# 12-5 ②：负向测试——用明文 HTTP 端点读同一个对象，期望被桶策略拒绝（403）。
# 用法：./scripts/negative-tls.sh [region]
set -uo pipefail
cd "$(dirname "$0")/.."
REGION="${1:-us-east-1}"; export AWS_PAGER=""
B="$(terraform output -raw bucket_name)"
echo "== HTTPS（应成功）"
aws s3api head-object --region "$REGION" --bucket "$B" --key lab/sample.txt --query ContentLength --output text
echo "== HTTP（应 403 Forbidden：DenyInsecureTransport）"
aws s3api head-object --region "$REGION" --bucket "$B" --key lab/sample.txt \
  --endpoint-url "http://s3.${REGION}.amazonaws.com" --query ContentLength --output text 2>&1 | tail -1
