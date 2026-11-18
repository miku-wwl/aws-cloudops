#!/usr/bin/env bash
# ② 立即发起一次按需备份，轮询到终态，保存恢复点 ARN。非 COMPLETED 一律停止。
set -euo pipefail
cd "$(dirname "$0")/.." && source scripts/_common.sh
JOB=$(aws backup start-backup-job --region "$REGION" --backup-vault-name "$(terraform output -raw vault_name)" \
      --resource-arn "$(terraform output -raw table_arn)" --iam-role-arn "$(terraform output -raw backup_role_arn)" \
      --query BackupJobId --output text)
echo "BackupJobId=$JOB"
while :; do
  read -r STATE RP <<< "$(aws backup describe-backup-job --region "$REGION" --backup-job-id "$JOB" --query '[State,RecoveryPointArn]' --output text)"
  case "$STATE" in
    COMPLETED) break ;;
    FAILED | ABORTED | EXPIRED | PARTIAL) echo "备份作业 $STATE，停止"; exit 1 ;;
    *) sleep 10 ;;
  esac
done
echo "{\"backupJobId\":\"$JOB\",\"recoveryPointArn\":\"$RP\",\"completed\":\"$(date -u +%FT%TZ)\"}" > state/backup.json
echo "恢复点：$RP"
