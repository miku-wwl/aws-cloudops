#!/usr/bin/env bash
# 第 19 讲实验 19-3：跨服务、按区域的只读残留盘点（全部为免费的只读 API）。
#   REGIONS="us-east-1 us-west-2" bash inventory.sh | tee inventory-$(date +%F).txt
# 最后两行是“覆盖范围”与失败的查询：没查到 ≠ 没有；没查的区域、没权限的服务都不能算“已清理”。
set -uo pipefail
REGIONS=${REGIONS:-us-east-1}
fail=()
run() { local out; out=$("$@" 2>&1) || { fail+=("$*"); echo "ERR"; return; }; echo "$out"; }
row() { printf '%-15s %-26s %s\n' "$1" "$2" "$3"; }

row region resource count
for r in $REGIONS; do
  row "$r" "ec2-instances(not-term)" "$(run aws ec2 describe-instances --region "$r" --filters Name=instance-state-name,Values=pending,running,stopping,stopped --query 'length(Reservations[].Instances[])' --output text)"
  row "$r" "ebs-volumes"             "$(run aws ec2 describe-volumes --region "$r" --query 'length(Volumes)' --output text)"
  row "$r" "ebs-snapshots(self)"     "$(run aws ec2 describe-snapshots --region "$r" --owner-ids self --query 'length(Snapshots)' --output text)"
  row "$r" "elastic-ip"              "$(run aws ec2 describe-addresses --region "$r" --query 'length(Addresses)' --output text)"
  row "$r" "nat-gateways"            "$(run aws ec2 describe-nat-gateways --region "$r" --filter Name=state,Values=available --query 'length(NatGateways)' --output text)"
  row "$r" "interface-endpoints"     "$(run aws ec2 describe-vpc-endpoints --region "$r" --filters Name=vpc-endpoint-type,Values=Interface --query 'length(VpcEndpoints)' --output text)"
  row "$r" "log-groups"              "$(run aws logs describe-log-groups --region "$r" --query 'length(logGroups)' --output text)"
  row "$r" "  never-expire"          "$(run aws logs describe-log-groups --region "$r" --query 'length(logGroups[?retentionInDays==null])' --output text)"
  row "$r" "backup-points(Default)"  "$(aws backup list-recovery-points-by-backup-vault --region "$r" --backup-vault-name Default --query 'length(RecoveryPoints)' --output text 2>/dev/null || echo '0 (no Default vault)')"
done
row global "s3-buckets" "$(run aws s3api list-buckets --query 'length(Buckets)' --output text)"
echo "coverage: regions=[$REGIONS] services=EC2,EBS,EIP,NAT,VPCE,Logs,Backup,S3"
echo "failed queries: ${#fail[@]} ${fail[*]:-}"
