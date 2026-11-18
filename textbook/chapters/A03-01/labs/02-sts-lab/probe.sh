#!/usr/bin/env bash
# 第 06 讲实验 6-3：扮演角色，以角色会话身份读取两个对象。
# 用法：./probe.sh <role-arn> <bucket> [session-policy.json]
# 临时凭证只存在于子 shell 的环境变量中，不写文件、不打印 SecretAccessKey。
set -uo pipefail
ROLE="${1:?role arn}"; BUCKET="${2:?bucket}"; SESSION_POLICY="${3:-}"
export AWS_PAGER="" MSYS_NO_PATHCONV=1

extra=()
[ -n "$SESSION_POLICY" ] && extra=(--policy "file://$SESSION_POLICY")

creds=$(aws sts assume-role --role-arn "$ROLE" --role-session-name "a06-probe-$(date +%s)" \
          --duration-seconds 900 "${extra[@]}" \
          --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' --output text) || {
  echo "AssumeRole 失败：检查信任策略中的 Principal、操作者自身权限、SCP"; exit 1; }

(
  read -r AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN <<<"$creds"
  export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
  echo "== 当前身份（应为 assumed-role 会话）"
  aws sts get-caller-identity --query Arn --output text
  for key in logs/health.txt reports/summary.csv; do
    if aws s3api get-object --bucket "$BUCKET" --key "$key" /dev/null >/dev/null 2>err.txt; then
      echo "✓ $key  exit=0"
    else
      echo "✗ $key  exit=$?  $(grep -o 'An error occurred ([A-Za-z]*)' err.txt)"
    fi
  done
  rm -f err.txt
)
