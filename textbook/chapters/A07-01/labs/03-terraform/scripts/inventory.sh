#!/usr/bin/env bash
# ⑤ 只读盘点：清理前确认本实验留下了什么（恢复点、恢复表）。
set -uo pipefail
cd "$(dirname "$0")/.." && source scripts/_common.sh
VAULT="$(terraform output -raw vault_name)"
echo "== $VAULT 中的恢复点"
aws backup list-recovery-points-by-backup-vault --region "$REGION" --backup-vault-name "$VAULT" \
  --query 'RecoveryPoints[].[RecoveryPointArn,Status,CreationDate]' --output text
echo "== 以 $TABLE 开头的表（恢复出的新表不归 Terraform 管，要手动删除）"
aws dynamodb list-tables --region "$REGION" --query "TableNames[?starts_with(@, '$TABLE')]" --output text
