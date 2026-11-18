#!/usr/bin/env bash
# 10-4 ②：对“一台”指定节点运行只读诊断文档，轮询到终态后打印输出。
# 用法：./scripts/diag.sh
#   - 只用 --instance-ids 指定一台，不用标签批量选目标；并发 1、容错 0
#   - --timeout-seconds 120：两分钟内送不到就放弃（DeliveryTimedOut），不必等默认的一小时
set -euo pipefail
cd "$(dirname "$0")/.." && source scripts/_common.sh && need_instance
DOC="$(terraform output -raw command_document)"

CMD=$(aws ssm send-command --region "$REGION" --document-name "$DOC" --instance-ids "$ID" \
      --max-concurrency 1 --max-errors 0 --timeout-seconds 120 --comment "a10 read-only diagnostics" \
      --query 'Command.CommandId' --output text)
echo "CommandId=$CMD"
for _ in $(seq 1 40); do
  STATUS=$(aws ssm get-command-invocation --region "$REGION" --command-id "$CMD" --instance-id "$ID" \
           --query 'Status' --output text 2>/dev/null || echo "Pending")
  case "$STATUS" in
    Pending | InProgress | Delayed) sleep 5 ;;
    *) break ;;
  esac
done
aws ssm get-command-invocation --region "$REGION" --command-id "$CMD" --instance-id "$ID" --output text \
  --query '[Status, StatusDetails, ResponseCode, StandardOutputContent, StandardErrorContent]'
