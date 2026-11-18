#!/usr/bin/env bash
# ① 写入 4 条订单，并在“备份之前”保存基线（强一致读）。
set -euo pipefail
cd "$(dirname "$0")/.." && source scripts/_common.sh
for i in 1:100:PAID 2:120:PAID 3:80:PENDING 4:50:PAID; do
  IFS=: read -r n amt st <<< "$i"
  aws dynamodb put-item --region "$REGION" --table-name "$TABLE" --item \
    "{\"pk\":{\"S\":\"TENANT#demo\"},\"sk\":{\"S\":\"ORDER#00$n\"},\"amount\":{\"N\":\"$amt\"},\"status\":{\"S\":\"$st\"}}"
done
aws dynamodb scan --region "$REGION" --table-name "$TABLE" --consistent-read --output json > state/baseline.json
"$PY" "$CANON" state/baseline.json state/baseline.json | head -2
echo "基线已保存：state/baseline.json（备份之前的 4 条）"
