#!/usr/bin/env bash
# 11-5 ②：复现事故——同事想“加一个 CostCenter 标签”，却用了整体替换的 PutBucketTagging。
# 用法：./scripts/drift.sh [region]       （只改实验桶的标签，不碰公共访问设置）
set -euo pipefail
cd "$(dirname "$0")/.."
REGION="${1:-us-east-1}"; export AWS_PAGER=""
BUCKET="$(terraform output -raw bucket_name)"
echo "执行时间（UTC）：$(date -u +%Y-%m-%dT%H:%M:%SZ)"
aws s3api put-bucket-tagging --region "$REGION" --bucket "$BUCKET" --tagging "file://scripts/tag-drift.json"
aws s3api get-bucket-tagging --region "$REGION" --bucket "$BUCKET" --query 'TagSet[].[Key,Value]' --output text
echo "Owner 已不在标签集中。几分钟后运行 ./scripts/investigate.sh 取证；恢复用 terraform apply。"
