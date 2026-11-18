#!/usr/bin/env bash
# 9-4 ⑤：只读查看最近 15 分钟的投递链指标——判断事件“卡”在哪一层。
# 用法：./scripts/check.sh [region]
set -euo pipefail
cd "$(dirname "$0")/.." && source scripts/_common.sh
REGION="${1:-us-east-1}"
BUS="$(terraform output -raw event_bus_name)"
RULE="$(terraform output -raw anomaly_rule_name)"
START="$(date -u -d '-15 min' +%Y-%m-%dT%H:%M:%SZ)"
END="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "== AWS/Events（EventBusName=$BUS, RuleName=$RULE）最近 15 分钟 Sum；None = 没有数据点"
for M in MatchedEvents Invocations FailedInvocations InvocationsSentToDlq InvocationsFailedToBeSentToDlq; do
  V=$(aws cloudwatch get-metric-statistics --region "$REGION" --namespace AWS/Events --metric-name "$M" \
      --dimensions Name=EventBusName,Value="$BUS" Name=RuleName,Value="$RULE" --statistics Sum --period 60 \
      --start-time "$START" --end-time "$END" --query 'sum(Datapoints[].Sum)' --output text)
  printf '  %-32s %s\n' "$M" "$V"
done

NS_METRIC="$(terraform output -raw metric)"
NS="${NS_METRIC% / *}"
echo "== $NS / Http5xx（指标过滤器只统计它创建之后写入的日志）"
aws cloudwatch get-metric-statistics --region "$REGION" --namespace "$NS" --metric-name Http5xx --statistics Sum \
  --period 60 --start-time "$START" --end-time "$END" --query 'sort_by(Datapoints,&Timestamp)[].[Timestamp,Sum]' --output text
