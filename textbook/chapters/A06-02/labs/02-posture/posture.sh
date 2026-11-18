#!/usr/bin/env bash
# 第 12 讲实验 12-2：只读盘点本区域的检测服务与数据保护基线，输出前替换账户号。
# 用法：./posture.sh [region]
set -uo pipefail
REGION="${1:-us-east-1}"; export AWS_PAGER=""
ACC="$(aws sts get-caller-identity --query Account --output text)"
mask() { sed -E "s/${ACC}/111122223333/g"; }
line() { printf '%-26s %s\n' "$1" "$(cat | tr '\n' ' ' | mask)"; }
aws guardduty list-detectors --region "$REGION" --query 'length(DetectorIds)' --output text 2>&1 | line "GuardDuty 检测器数"
aws securityhub describe-hub --region "$REGION" --query HubArn --output text 2>&1 | tail -1 | line "Security Hub CSPM"
aws inspector2 batch-get-account-status --region "$REGION" --query 'accounts[0].state.status' --output text 2>&1 | line "Inspector"
aws macie2 get-macie-session --region "$REGION" --query status --output text 2>&1 | tail -1 | line "Macie"
aws s3control get-public-access-block --account-id "$ACC" --region "$REGION" \
  --query 'PublicAccessBlockConfiguration' --output text 2>&1 | tail -1 | line "账户级 S3 BPA"
aws kms describe-key --region "$REGION" --key-id alias/aws/s3 --query 'KeyMetadata.[KeyManager,KeyState]' --output text 2>&1 | line "AWS 托管密钥 aws/s3"
aws kms list-keys --region "$REGION" --query 'length(Keys)' --output text 2>&1 | line "本区域 KMS 密钥总数"
