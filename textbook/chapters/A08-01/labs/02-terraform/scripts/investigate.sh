#!/usr/bin/env bash
# 14-3 ③：取证（全部只读）——事件、现状、对照。
set -uo pipefail
cd "$(dirname "$0")/.."
export AWS_PAGER=""; REGION="${REGION:-us-east-1}"; PY=python3; "$PY" -c "import sys" >/dev/null 2>&1 || PY=python
SG="$(terraform output -raw security_group_id)"
echo "== 事件：按资源名（SG ID）查最近 2 小时"
"$PY" ../../../A06-01/labs/02-ctquery/ctquery.py --resource "$SG" --hours 2 --region "$REGION" --max 10
echo "== 现状：该 SG 的全部规则"
aws ec2 describe-security-group-rules --region "$REGION" --filters Name=group-id,Values="$SG" --output table \
  --query 'SecurityGroupRules[].{Id:SecurityGroupRuleId,Egress:IsEgress,Proto:IpProtocol,From:FromPort,Cidr:CidrIpv4}'
echo "== 对照：同一时间窗内路由与 NACL 是否有变更事件"
for n in ReplaceRoute CreateRoute DeleteRoute ReplaceNetworkAclEntry CreateNetworkAclEntry DeleteNetworkAclEntry; do
  printf '  %-26s %s\n' "$n" "$(aws cloudtrail lookup-events --region "$REGION" --lookup-attributes AttributeKey=EventName,AttributeValue=$n \
     --start-time "$(date -u -d '-2 hours' +%FT%TZ)" --query 'length(Events)' --output text)"
done
echo "== Terraform 视角：漂移（应只看到这一条入站规则需要重新创建）"
if [ -n "${CLIENT_CIDR:-}" ]; then
  terraform plan -input=false -no-color -var client_cidr="$CLIENT_CIDR" | grep -E "^  # |^Plan:"
else
  echo "  设置 CLIENT_CIDR=<你的公网IP>/32 后再运行，可直接看到 plan 摘要"
fi
