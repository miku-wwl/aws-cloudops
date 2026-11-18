#!/usr/bin/env bash
# 10-4 ⑤：terraform destroy 之后，用与 Terraform 无关的查询独立核对“没有遗留”（全部只读）。
# 用法：./scripts/after-destroy.sh [region]
set -uo pipefail
REGION="${1:-us-east-1}"
export AWS_PAGER=""
echo "== 仍带 Chapter=A05-01 标签、未终止的实例（应为空）"
aws ec2 describe-instances --region "$REGION" --filters Name=tag:Chapter,Values=A05-01 \
  Name=instance-state-name,Values=pending,running,stopping,stopped \
  --query 'Reservations[].Instances[].[InstanceId,State.Name]' --output text
echo "== 仍带标签的 EBS 卷（应为空；根卷 delete_on_termination=true）"
aws ec2 describe-volumes --region "$REGION" --filters Name=tag:Chapter,Values=A05-01 --query 'Volumes[].[VolumeId,State]' --output text
echo "== 未关联的弹性 IP / 公网 IPv4（本实验不分配 EIP，应为空）"
aws ec2 describe-addresses --region "$REGION" --query 'Addresses[?AssociationId==null].[PublicIp,AllocationId]' --output text
echo "== 本实验的 SSM 文档（应为空）"
aws ssm list-documents --region "$REGION" --filters Key=Owner,Values=Self Key=Name,Values=a10- \
  --query 'DocumentIdentifiers[].Name' --output text
echo "== 本实验的 IAM 角色（应为空）"
aws iam list-roles --query "Roles[?starts_with(RoleName, 'a10-')].RoleName" --output text
