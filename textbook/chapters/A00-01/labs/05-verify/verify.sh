#!/usr/bin/env bash
# A00-01 实验 6：Landing Zone 落地后的验收（只读）。
# 用法：./verify.sh <home-region> <ou-arn> [member-account-id]
set -uo pipefail
REGION="${1:?home region}"; OU_ARN="${2:?target OU ARN}"; ACCOUNT="${3:-}"
export AWS_PAGER=""

LZ=$(aws controltower list-landing-zones --region "$REGION" --query 'landingZones[0].arn' --output text)
[ "$LZ" = "None" ] && { echo "没有 Landing Zone"; exit 1; }

echo "== 证据 1：Landing Zone 版本 / 状态 / 漂移"
aws controltower get-landing-zone --region "$REGION" --landing-zone-identifier "$LZ" \
  --query 'landingZone.{version:version,status:status,drift:driftStatus.status,latest:latestAvailableVersion,remediation:remediationTypes}' --output table

echo "== 证据 2：线上 manifest（与 Terraform 的 manifest_preview 对比）"
aws controltower get-landing-zone --region "$REGION" --landing-zone-identifier "$LZ" \
  --query 'landingZone.manifest' --output json > manifest-live.json && echo "已保存 manifest-live.json"

echo "== 证据 3：目标 OU 及其子账户的基线状态（includeChildren）"
aws controltower list-enabled-baselines --region "$REGION" --include-children \
  --query 'enabledBaselines[].{target:targetIdentifier,version:baselineVersion,status:statusSummary.status,drift:driftStatusSummary.driftStatus}' \
  --output table

echo "== 证据 4：目标 OU 上的控制"
aws controltower list-enabled-controls --region "$REGION" --target-identifier "$OU_ARN" \
  --query 'enabledControls[].{control:controlIdentifier,status:statusSummary.status,drift:driftStatusSummary.driftStatus}' --output table

echo "== 证据 5：组织级 CloudTrail（centralizedLogging 启用时存在）"
aws cloudtrail describe-trails --region "$REGION" --query 'trailList[?IsOrganizationTrail].{name:Name,bucket:S3BucketName,multiRegion:IsMultiRegionTrail}' --output table

if [ -n "$ACCOUNT" ]; then
  echo "== 证据 6：成员账户所在 OU"
  aws organizations list-parents --child-id "$ACCOUNT" --query 'Parents[0]' --output table
fi
