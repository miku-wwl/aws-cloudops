#!/usr/bin/env bash
# 第 12 讲实验 12-3：用 IAM 策略模拟器验证“桶策略这道门”，并观察它对 KMS 密钥策略的局限。
# 只做计算、不收费。用法：./policysim.sh
set -uo pipefail
cd "$(dirname "$0")"; export AWS_PAGER=""
CALLER=arn:aws:iam::111122223333:user/a12-reader
OWNER=arn:aws:iam::111122223333:root
OBJ=arn:aws:s3:::a12-demo/lab/sample.txt
KEY=arn:aws:kms:us-east-1:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab
sim() {  # $1=说明 $2=身份策略 $3=资源策略 $4=动作 $5=资源 其余=上下文
  local d="$1" ip="$2" rp="$3" act="$4" res="$5"; shift 5
  local ctx=(); [ $# -gt 0 ] && ctx=(--context-entries "$@")
  printf '%-44s %s\n' "$d" "$(aws iam simulate-custom-policy --policy-input-list "$(cat "$ip")" --resource-policy "$(cat "$rp")" \
    --caller-arn "$CALLER" --resource-owner "$OWNER" --action-names "$act" --resource-arns "$res" "${ctx[@]}" \
    --query 'EvaluationResults[0].EvalDecision' --output text 2>&1 | tail -1)"
}
echo "== S3 门：桶策略（模拟器可以正确评估）"
sim "GetObject，HTTPS，TLS 1.3" reader-policy.json bucket-policy.json s3:GetObject "$OBJ" \
  ContextKeyName=aws:SecureTransport,ContextKeyValues=true,ContextKeyType=boolean ContextKeyName=s3:TlsVersion,ContextKeyValues=1.3,ContextKeyType=numeric
sim "GetObject，HTTP（无 TLS）" reader-policy.json bucket-policy.json s3:GetObject "$OBJ" \
  ContextKeyName=aws:SecureTransport,ContextKeyValues=false,ContextKeyType=boolean
sim "GetObject，HTTPS，TLS 1.1" reader-policy.json bucket-policy.json s3:GetObject "$OBJ" \
  ContextKeyName=aws:SecureTransport,ContextKeyValues=true,ContextKeyType=boolean ContextKeyName=s3:TlsVersion,ContextKeyValues=1.1,ContextKeyType=numeric
echo "== KMS 门：密钥策略（模拟器按通用规则评估，结果不能代表 KMS）"
sim "Decrypt：密钥策略只授权 a12-app，调用者无 KMS 权限" reader-policy.json key-policy-no-delegation.json kms:Decrypt "$KEY"
sim "Decrypt：同上，但调用者的身份策略允许 kms:Decrypt" reader-with-kms-policy.json key-policy-no-delegation.json kms:Decrypt "$KEY"
echo "（真实 KMS 中第二条也会被拒绝：密钥策略既未点名调用者，也未委托给本账户 IAM。）"
