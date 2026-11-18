#!/usr/bin/env bash
# 11-5 ③：三份证据各回答一个问题（全部只读）
#   行为（CloudTrail 事件历史）：谁、何时、调用了什么
#   现状（S3 API）：此刻的标签集
#   评价（AWS Config）：规则何时判定不合规、配置项历史
# 用法：./scripts/investigate.sh [region] [回看小时数]
set -uo pipefail
cd "$(dirname "$0")/.."
REGION="${1:-us-east-1}"; HOURS="${2:-2}"; export AWS_PAGER=""
BUCKET="$(terraform output -raw bucket_name)"; RULE="$(terraform output -raw config_rule_name 2>/dev/null || true)"
PY=python3; "$PY" -c "import sys" >/dev/null 2>&1 || PY=python
echo "== ① 行为：CloudTrail 事件历史（按资源名 $BUCKET）"
"$PY" ../02-ctquery/ctquery.py --resource "$BUCKET" --hours "$HOURS" --region "$REGION" --max 20
echo "== ② 现状：当前标签"
aws s3api get-bucket-tagging --region "$REGION" --bucket "$BUCKET" --query 'TagSet[].[Key,Value]' --output text
if [ -n "$RULE" ] && [ "$RULE" != "null" ]; then
  echo "== ③ 评价：规则 $RULE 的结果"
  aws configservice get-compliance-details-by-config-rule --region "$REGION" --config-rule-name "$RULE" \
    --query 'EvaluationResults[].[EvaluationResultIdentifier.EvaluationResultQualifier.ResourceId,ComplianceType,ResultRecordedTime]' --output text
  echo "== ③ 配置项历史（最近 5 个）"
  aws configservice get-resource-config-history --region "$REGION" --resource-type AWS::S3::Bucket --resource-id "$BUCKET" \
    --limit 5 --query 'configurationItems[].[configurationItemCaptureTime,configurationItemStatus,tags.Owner]' --output text
else
  echo "== ③ 未启用 Config：没有规则评估。注意——“没有评估结果”不等于“合规”。"
fi
