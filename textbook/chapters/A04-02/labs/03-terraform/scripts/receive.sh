#!/usr/bin/env bash
# 9-4 ④：长轮询 10 秒读取值班队列（--dlq 读死信队列）。默认只读不删；加 --delete 才确认消费。
# 用法：./scripts/receive.sh [region] [--dlq] [--delete]
set -euo pipefail
cd "$(dirname "$0")/.." && source scripts/_common.sh
REGION="us-east-1"
OUT="queue_url"
DELETE=0
for a in "$@"; do
  case "$a" in
    --dlq) OUT="dlq_url" ;;
    --delete) DELETE=1 ;;
    *) REGION="$a" ;;
  esac
done
URL="$(terraform output -raw "$OUT")"
RESP="$(mktemp)"

aws sqs receive-message --region "$REGION" --queue-url "$URL" --wait-time-seconds 10 --max-number-of-messages 10 \
  --message-attribute-names All --message-system-attribute-names ApproximateReceiveCount --output json \
  > "$RESP"

"$PY" - "$RESP" "$DELETE" <<'PYEOF' | while read -r HANDLE; do
import json, sys
raw = open(sys.argv[1], encoding="utf-8").read().strip()
msgs = json.loads(raw).get("Messages", []) if raw else []
print(f"收到 {len(msgs)} 条", file=sys.stderr)
for m in msgs:
    print("-- 第 %s 次被读取" % m["Attributes"]["ApproximateReceiveCount"], file=sys.stderr)
    print(json.dumps(json.loads(m["Body"]), ensure_ascii=False, indent=2), file=sys.stderr)
    for k, v in m.get("MessageAttributes", {}).items():   # DLQ 消息带 ERROR_CODE、ERROR_MESSAGE、RULE_ARN 等
        print(f"   {k} = {v.get('StringValue')}", file=sys.stderr)
    if sys.argv[2] == "1":
        print(m["ReceiptHandle"])                          # 只有要删除时才把句柄交给下游
PYEOF
  aws sqs delete-message --region "$REGION" --queue-url "$URL" --receipt-handle "$HANDLE"
  echo "已删除一条（确认消费）"
done
[ "$DELETE" = 1 ] || echo "未删除：这些消息会在可见性超时（30 秒）后重新可见。"
rm -f "$RESP"
