#!/usr/bin/env bash
# 第 10 讲实验 10-4 ①：分层查看实验节点（全部只读）。
#   EC2 层：实例状态、实例配置文件、IMDS 设置
#   网络层：安全组出站规则
#   SSM 层：PingStatus、Agent 版本、最后一次心跳
# 用法（在 03-terraform 目录）：./scripts/status.sh
set -euo pipefail
cd "$(dirname "$0")/.." && source scripts/_common.sh && need_instance
SG="$(terraform output -raw security_group_id)"

echo "== EC2"
aws ec2 describe-instances --region "$REGION" --instance-ids "$ID" --output table \
  --query 'Reservations[0].Instances[0].{State:State.Name,Profile:IamInstanceProfile.Arn,IMDSv2:MetadataOptions.HttpTokens,PublicIp:PublicIpAddress}'
echo "== 安全组出站规则（应只有 TCP 443；为空即故障注入状态）"
aws ec2 describe-security-group-rules --region "$REGION" --filters Name=group-id,Values="$SG" --output table \
  --query 'SecurityGroupRules[].{Egress:IsEgress,Proto:IpProtocol,From:FromPort,To:ToPort,Cidr:CidrIpv4}'
echo "== SSM（查不到 = 从未注册）"
aws ssm describe-instance-information --region "$REGION" --filters Key=InstanceIds,Values="$ID" --output table \
  --query 'InstanceInformationList[].{Ping:PingStatus,LastPing:LastPingDateTime,Agent:AgentVersion,Platform:PlatformName}'
