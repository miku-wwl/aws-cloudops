#!/usr/bin/env bash
# 第 15 讲实验 15-2：用 IAM 策略模拟器验证“只能碰 dev 环境的状态与锁”（只做计算、不收费）。
set -uo pipefail
cd "$(dirname "$0")"; export AWS_PAGER=""
POL="$(cat state-access-policy.json)"; B=arn:aws:s3:::a15-lab01-state
sim() { printf '%-18s %-52s %s\n' "$1" "$2" "$(aws iam simulate-custom-policy --policy-input-list "$POL" --action-names "$1" --resource-arns "$2" "${@:3}" --query 'EvaluationResults[0].EvalDecision' --output text 2>&1 | tail -1)"; }
sim s3:GetObject    "$B/platform/dev/terraform.tfstate"
sim s3:PutObject    "$B/platform/dev/terraform.tfstate"
sim s3:DeleteObject "$B/platform/dev/terraform.tfstate"
sim s3:PutObject    "$B/platform/dev/terraform.tfstate.tflock"
sim s3:DeleteObject "$B/platform/dev/terraform.tfstate.tflock"
sim s3:GetObject    "$B/platform/prod/terraform.tfstate"
sim s3:ListBucket   "$B" --context-entries ContextKeyName=s3:prefix,ContextKeyValues=platform/dev/,ContextKeyType=string
sim s3:ListBucket   "$B" --context-entries ContextKeyName=s3:prefix,ContextKeyValues=platform/prod/,ContextKeyType=string
