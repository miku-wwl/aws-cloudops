#!/usr/bin/env bash
# 第 16 讲实验 16-3：用 IAM Access Analyzer 校验三份 GitHub OIDC 信任策略（只读计算 API，免费，不创建任何资源）。
#   bash validate.sh > validate-$(date +%F).txt
set -euo pipefail
cd "$(dirname "$0")"
for f in trust-plan-role.json trust-apply-role.json trust-apply-role-with-ref.json; do
  echo "== $f"
  aws accessanalyzer validate-policy \
    --policy-type RESOURCE_POLICY \
    --validate-policy-resource-type AWS::IAM::AssumeRolePolicyDocument \
    --policy-document "$(cat "$f")" \
    --query 'findings[].[findingType,issueCode]' --output text | tr -d '\r'
done
