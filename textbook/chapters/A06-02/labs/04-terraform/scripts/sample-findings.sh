#!/usr/bin/env bash
# 12-5 ③（仅 enable_guardduty=true）：生成一条 S3 类样例 Finding，确认它带 [SAMPLE] 标记。
# 样例 Finding 用于测试展示、筛选与自动化，不代表真实攻击。
set -euo pipefail
cd "$(dirname "$0")/.."
REGION="${1:-us-east-1}"; export AWS_PAGER=""
D="$(terraform output -raw detector_id)"
[ -n "$D" ] && [ "$D" != "null" ] || { echo "未启用 GuardDuty（enable_guardduty=false）"; exit 1; }
aws guardduty create-sample-findings --region "$REGION" --detector-id "$D" \
  --finding-types "Exfiltration:S3/AnomalousBehavior"
sleep 5
IDS=$(aws guardduty list-findings --region "$REGION" --detector-id "$D" --max-results 5 --query 'FindingIds' --output text)
aws guardduty get-findings --region "$REGION" --detector-id "$D" --finding-ids $IDS \
  --query 'Findings[].[Type,Title,Service.AdditionalInfo.Value,Severity]' --output text
