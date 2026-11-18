#!/usr/bin/env bash
# A00-01 实验 1：只读预检 —— 当前身份、组织状态、Landing Zone 状态、可用基线与控制。
# 不创建、不修改任何资源。所需权限：sts:GetCallerIdentity、organizations:Describe*/List*、
# controltower:List*/Get*、controlcatalog:List*。用法：./preflight.sh [home-region]
set -uo pipefail
HOME_REGION="${1:-us-east-1}"
export AWS_PAGER=""

say() { printf '\n== %s\n' "$*"; }

say "1. 当前身份"
aws sts get-caller-identity --query '{Account:Account,Arn:Arn}' --output table || exit 1

say "2. 组织状态"
if org_json=$(aws organizations describe-organization --output json 2>&1); then
  echo "$org_json" | grep -E '"(Id|FeatureSet|MasterAccountId)"'
  me=$(aws sts get-caller-identity --query Account --output text)
  mgmt=$(echo "$org_json" | sed -n 's/.*"MasterAccountId": "\([0-9]*\)".*/\1/p')
  if [ "$me" = "$mgmt" ]; then echo "→ 本账户是组织的管理账户。"; else echo "→ 本账户是成员账户：Control Tower 只能在管理账户中设置。"; fi
else
  case "$org_json" in
    *AWSOrganizationsNotInUseException*) echo "→ 不属于任何组织：控制台向导第 2 步会新建组织，本账户将成为管理账户（之后不能更换）。" ;;
    *AccessDenied*) echo "→ 无权限：AccessDenied 不等于组织不存在，请换用有 organizations 读权限的身份。" ;;
    *) echo "$org_json" ;;
  esac
fi

say "3. Landing Zone（Home Region = $HOME_REGION）"
lz=$(aws controltower list-landing-zones --region "$HOME_REGION" --query 'landingZones[0].arn' --output text 2>&1)
case "$lz" in
  None|"") echo "→ 该区域没有 Landing Zone。若组织已存在，仍需在其他区域确认（LZ 只存在于其 Home Region）。" ;;
  arn:*)   echo "→ 已有 Landing Zone：$lz（不要重复创建，改看状态与版本）"
           aws controltower get-landing-zone --region "$HOME_REGION" --landing-zone-identifier "$lz" \
             --query 'landingZone.{version:version,status:status,drift:driftStatus.status,latest:latestAvailableVersion}' --output table ;;
  *)       echo "$lz" ;;
esac

say "4. 可用基线（ARN 与区域相关，Terraform 中要用）"
aws controltower list-baselines --region "$HOME_REGION" --query 'baselines[].[name,arn]' --output table

say "5. Control Catalog：按行为统计控制数量"
aws controlcatalog list-controls --region "$HOME_REGION" --query 'Controls[].Behavior' --output text \
  | tr -s '[:space:]' '\n' | sed '/^$/d' | sort | uniq -c
