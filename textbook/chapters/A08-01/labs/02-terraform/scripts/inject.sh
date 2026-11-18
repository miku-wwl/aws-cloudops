#!/usr/bin/env bash
# 14-3 ②：只注入一个故障——按规则 ID 删除那一条 TCP 80 入站规则。记录 UTC 时间。
set -euo pipefail
cd "$(dirname "$0")/.."
export AWS_PAGER=""; REGION="${REGION:-us-east-1}"
SG="$(terraform output -raw security_group_id)"; RULE="$(terraform output -raw ingress_rule_id)"
echo "注入时间（UTC）：$(date -u +%FT%TZ)  SG=$SG  规则=$RULE"
aws ec2 revoke-security-group-ingress --region "$REGION" --group-id "$SG" --security-group-rule-ids "$RULE" --query Return --output text
