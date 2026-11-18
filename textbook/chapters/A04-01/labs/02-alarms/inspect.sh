#!/usr/bin/env bash
# 第 08 讲实验 8-3：只读查看告警状态、状态原因与最近的状态变化。
# 用法：./inspect.sh [region] [service]
set -uo pipefail
REGION="${1:-us-east-1}"; SERVICE="${2:-checkout}"; export AWS_PAGER=""
aws cloudwatch describe-alarms --region "$REGION" --alarm-name-prefix "a08-$SERVICE" \
  --alarm-types MetricAlarm CompositeAlarm \
  --query '[MetricAlarms[].{Name:AlarmName,State:StateValue,Since:StateUpdatedTimestamp}, CompositeAlarms[].{Name:AlarmName,State:StateValue,Since:StateUpdatedTimestamp}][]' \
  --output table
echo "== 状态变化历史（最近 10 条）"
aws cloudwatch describe-alarm-history --region "$REGION" --alarm-name "a08-$SERVICE-errors" \
  --history-item-type StateUpdate --max-items 10 \
  --query 'AlarmHistoryItems[].[Timestamp,HistorySummary]' --output text
echo "== 最近 20 分钟 Errors(Sum)"
aws cloudwatch get-metric-statistics --region "$REGION" --namespace Lab/CloudOps --metric-name Errors \
  --dimensions Name=Service,Value="$SERVICE" --statistics Sum --period 60 \
  --start-time "$(date -u -d '-20 min' +%Y-%m-%dT%H:%M:%SZ)" --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --query 'sort_by(Datapoints,&Timestamp)[].[Timestamp,Sum]' --output text
