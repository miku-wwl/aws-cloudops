#!/usr/bin/env bash
# 10-4 ③：运行盘点 Runbook（只调用控制面 API，不经过节点上的 Agent）。
# 用法：./scripts/inventory.sh
# 调用者需要 ssm:StartAutomationExecution，以及把执行角色传给 SSM 的 iam:PassRole（见实验 10-2）。
set -euo pipefail
cd "$(dirname "$0")/.." && source scripts/_common.sh && need_instance
DOC="$(terraform output -raw automation_document)"

EXE=$(aws ssm start-automation-execution --region "$REGION" --document-name "$DOC" \
      --parameters "InstanceId=$ID" --query 'AutomationExecutionId' --output text)
echo "AutomationExecutionId=$EXE"
for _ in $(seq 1 30); do
  STATUS=$(aws ssm get-automation-execution --region "$REGION" --automation-execution-id "$EXE" \
           --query 'AutomationExecution.AutomationExecutionStatus' --output text)
  case "$STATUS" in
    Pending | InProgress | Waiting) sleep 3 ;;
    *) break ;;
  esac
done
aws ssm get-automation-execution --region "$REGION" --automation-execution-id "$EXE" --output json \
  --query 'AutomationExecution.{Status:AutomationExecutionStatus,Outputs:Outputs,Failure:FailureMessage}'
