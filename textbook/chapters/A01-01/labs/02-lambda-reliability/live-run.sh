#!/usr/bin/env bash
# V1.1 实测脚本（生成 live-2026-11-19.txt 所用的原样脚本）。会在 AWS 中创建并销毁 10 个资源，费用估算 < 0.01 美元。
# 用法：bash live-run.sh <本目录> <装有 boto3 的 python> <provider 缓存目录> 2>&1 | sed -E "s/<账户号>/111122223333/g; s#user/<用户名>#user/ops-admin#g" > live-<日期>.txt
# 退出时 trap 一定执行 terraform destroy 与残留检查；同名资源已存在时直接停止。
set -uo pipefail
LAB=$1; PY=$2; PLUG=$3
export MSYS_NO_PATHCONV=1 AWS_PAGER="" AWS_DEFAULT_REGION=us-east-1 TF_IN_AUTOMATION=1 PYTHONIOENCODING=utf-8
FN=ticket-query
log() { echo; echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }
TF() { terraform -chdir="$LAB" "$@" -no-color -input=false; }
alarms() { aws cloudwatch describe-alarms --alarm-name-prefix "$FN-" --alarm-types MetricAlarm CompositeAlarm \
  --query '[MetricAlarms[].[AlarmName,StateValue],CompositeAlarms[].[AlarmName,StateValue]][][]' --output text | tr -d '\r' | sort; }
state() { aws cloudwatch describe-alarms --alarm-names "$1" --alarm-types MetricAlarm CompositeAlarm \
  --query '[MetricAlarms[0].StateValue,CompositeAlarms[0].StateValue]' --output text | tr -d '\r' | tr '\t' '\n' | grep -v None | head -1; }
wait_state() { local t=0 s=""; while [ "$t" -le "$3" ]; do s=$(state "$1"); [ "$s" = "$2" ] && { echo "  $1 -> $2（等待 ${t} s）"; return 0; }; sleep 20; t=$((t + 20)); done
  echo "  $1 在 $3 s 内没有变为 $2（当前 $s）"; return 1; }
probe() { (cd "$LAB" && "$PY" probe.py --function-name "$FN" --count "$1"); }
mtrc() { aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name "$1" --dimensions Name=FunctionName,Value=$FN \
  --start-time "$(date -u -d '-20 min' +%FT%TZ)" --end-time "$(date -u +%FT%TZ)" --period 300 --statistics Sum \
  --query 'sort_by(Datapoints,&Timestamp)[].[Timestamp,Sum]' --output text | tr -d '\r' | sed "s/^/  $1 /"; }
residual() {
  log "== 残留检查（destroy 之后）"
  echo "  Lambda 函数：$(aws lambda get-function --function-name $FN 2>&1 | grep -oE 'ResourceNotFoundException|"FunctionName"' | head -1)"
  echo "  告警：$(aws cloudwatch describe-alarms --alarm-name-prefix "$FN-" --alarm-types MetricAlarm CompositeAlarm --query 'length(MetricAlarms)+length(CompositeAlarms)' --output text | tr -d '\r') 个"
  echo "  日志组：$(aws logs describe-log-groups --log-group-name-prefix /aws/lambda/$FN --query 'length(logGroups)' --output text | tr -d '\r') 个"
  echo "  IAM 角色：$(aws iam get-role --role-name $FN-role 2>&1 | grep -oE 'NoSuchEntity|"RoleName"' | head -1)"
  echo "  状态中的资源：$(terraform -chdir="$LAB" state list | wc -l) 个（terraform state list）"
}
cleanup() { log "== D 销毁（trap，无论前面成功与否都执行）"; TF destroy -auto-approve 2>&1 | grep -E 'Destroy complete|Error' ; residual; }

log "== 0 预检：同名资源必须不存在（不触碰非实验资源）"
pre=$(aws lambda get-function --function-name $FN 2>&1 | grep -c '"FunctionName"'); pre2=$(aws cloudwatch describe-alarms --alarm-name-prefix "$FN-" --query 'length(MetricAlarms)' --output text | tr -d '\r')
echo "  同名函数 $pre 个，同名告警 $pre2 个"
[ "$pre" = 0 ] && [ "$pre2" = 0 ] || { echo "  已存在同名资源，停止"; exit 1; }
mkdir -p "$PLUG"; export TF_PLUGIN_CACHE_DIR="$PLUG" TF_PLUGIN_CACHE_MAY_BREAK_DEPENDENCY_LOCK_FILE=true
TF init 2>&1 | grep -E 'Installed|Error' || true
[ -d "$LAB/.terraform/providers" ] || { echo "init 失败"; exit 1; }
trap cleanup EXIT

log "== A1 LIVE APPLY（fail_rate=0）"
TF apply -auto-approve 2>&1 | grep -E 'Apply complete|Error|error'
TF output -json burn_rate_thresholds 2>/dev/null | tr -d '\n ' ; echo
log "== A2 正常流量 200 次"
probe 200
wait_state "$FN-errors-any" OK 600; alarms

log "== B1 注入可逆故障：fail_rate=0.2（只改函数环境变量）"
TF apply -auto-approve -var fail_rate=0.2 2>&1 | grep -E 'Apply complete|FAIL_RATE|Error'
aws lambda wait function-updated --function-name $FN
echo "  环境变量：$(aws lambda get-function-configuration --function-name $FN --query 'Environment.Variables' --output text | tr -d '\r')"
log "== B2 故障流量 200 次"
probe 200
wait_state "$FN-errors-any" ALARM 600
wait_state "$FN-burn-fast-short" ALARM 900
wait_state "$FN-slo-page" ALARM 300
alarms
log "== B3 诊断证据"
mtrc Invocations; mtrc Errors
echo "  日志中的异常（前 2 条）："
aws logs filter-log-events --log-group-name /aws/lambda/$FN --filter-pattern '"injected failure"' --max-items 2 \
  --query 'events[].message' --output text 2>&1 | tr -d '\r' | tr '\t' '\n' | cut -c1-160 | sed 's/^/    /'

log "== C1 修复：fail_rate=0"
TF apply -auto-approve 2>&1 | grep -E 'Apply complete|FAIL_RATE|Error'
aws lambda wait function-updated --function-name $FN
echo "  环境变量：$(aws lambda get-function-configuration --function-name $FN --query 'Environment.Variables' --output text | tr -d '\r')"
log "== C2 恢复后流量 200 次"
probe 200
wait_state "$FN-errors-any" OK 600
wait_state "$FN-burn-fast-short" OK 900
wait_state "$FN-slo-page" OK 600
alarms
log "== C3 告警状态历史（StateUpdate）"
for a in errors-any burn-fast-short burn-fast-long slo-page; do
  aws cloudwatch describe-alarm-history --alarm-name "$FN-$a" --history-item-type StateUpdate --max-records 6 \
    --query 'sort_by(AlarmHistoryItems,&Timestamp)[].[Timestamp,HistorySummary]' --output text 2>&1 | tr -d '\r' | sed "s/^/  [$a] /" | cut -c1-170
done
mtrc Invocations; mtrc Errors
