#!/usr/bin/env bash
# ③ 备份完成之后再写第 5 条订单，然后把恢复点恢复到一张“新表”（不覆盖源表）。
set -euo pipefail
cd "$(dirname "$0")/.." && source scripts/_common.sh
RP="$("$PY" -c "import json;print(json.load(open('state/backup.json'))['recoveryPointArn'])")"
aws dynamodb put-item --region "$REGION" --table-name "$TABLE" --item \
  '{"pk":{"S":"TENANT#demo"},"sk":{"S":"ORDER#005"},"amount":{"N":"75"},"status":{"S":"PAID"}}'
TARGET="${TABLE}-restored-$(date -u +%H%M%S)"
JOB=$(aws backup start-restore-job --region "$REGION" --recovery-point-arn "$RP" \
      --iam-role-arn "$(terraform output -raw restore_role_arn)" \
      --metadata "targetTableName=$TARGET,encryptionType=Default" --query RestoreJobId --output text)
echo "RestoreJobId=$JOB  目标表=$TARGET"
while :; do
  STATUS=$(aws backup describe-restore-job --region "$REGION" --restore-job-id "$JOB" --query Status --output text)
  case "$STATUS" in
    COMPLETED) break ;;
    FAILED | ABORTED) aws backup describe-restore-job --region "$REGION" --restore-job-id "$JOB" --query StatusMessage --output text; exit 1 ;;
    *) sleep 15 ;;
  esac
done
aws dynamodb wait table-exists --region "$REGION" --table-name "$TARGET"
echo "$TARGET" > state/restored-table.txt
