#!/usr/bin/env bash
# 第 08 讲实验 8-3：向 Lab/CloudOps 上报三条指标（真实调用 PutMetricData）。
# 用法：./publish.sh <baseline|fault|recovery> [region] [service]
# 每隔 65 秒上报一组，共 3 组，保证落在 3 个不同的 1 分钟窗口。会产生少量自定义指标费用。
set -euo pipefail
PHASE="${1:?baseline|fault|recovery}"; REGION="${2:-us-east-1}"; SERVICE="${3:-checkout}"
case "$PHASE" in fault) ERR=2 ;; baseline|recovery) ERR=0 ;; *) echo "未知阶段 $PHASE"; exit 1 ;; esac
for i in 1 2 3; do
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  aws cloudwatch put-metric-data --region "$REGION" --namespace "Lab/CloudOps" --metric-data \
    "MetricName=Requests,Dimensions=[{Name=Service,Value=$SERVICE}],Timestamp=$TS,Value=100,Unit=Count" \
    "MetricName=Errors,Dimensions=[{Name=Service,Value=$SERVICE}],Timestamp=$TS,Value=$ERR,Unit=Count" \
    "MetricName=Heartbeat,Dimensions=[{Name=Service,Value=$SERVICE}],Timestamp=$TS,Value=1,Unit=Count"
  echo "[$TS] $PHASE：Requests=100 Errors=$ERR Heartbeat=1（第 $i/3 组）"
  [ "$i" -lt 3 ] && sleep 65
done
