#!/usr/bin/env bash
# 9-4 ②：用 API 运行一条保存的查询（StartQuery → 轮询 GetQueryResults），打印结果与扫描量。
# 用法：./scripts/query.sh <查询文件> [region] [回看分钟数，默认 15]
#   例：./scripts/query.sh ../queries/03-error-rate.cwli
set -euo pipefail
cd "$(dirname "$0")/.." && source scripts/_common.sh
QFILE="${1:?用法：query.sh ../queries/03-error-rate.cwli [region] [minutes]}"
REGION="${2:-us-east-1}"
MINUTES="${3:-15}"
GROUP="$(terraform output -raw log_group_name)"
END=$(date -u +%s)
START=$((END - MINUTES * 60))

QID=$(aws logs start-query --region "$REGION" --log-group-names "$GROUP" --start-time "$START" --end-time "$END" \
      --query-string "$(grep -v '^#' "$QFILE")" --query queryId --output text)
echo "queryId=$QID"
for _ in $(seq 1 60); do
  STATUS=$(aws logs get-query-results --region "$REGION" --query-id "$QID" --query status --output text)
  case "$STATUS" in
    Complete) break ;;
    Failed | Cancelled | Timeout | Unknown) echo "查询状态：$STATUS"; exit 1 ;;
  esac
  sleep 1
done

RESULT="$(mktemp)"
aws logs get-query-results --region "$REGION" --query-id "$QID" --output json > "$RESULT"
"$PY" - "$RESULT" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
rows = [{c["field"]: c["value"] for c in r if c["field"] != "@ptr"} for r in d["results"]]
keys = list(rows[0]) if rows else []
print("  ".join(keys))
for r in rows:
    print("  ".join(r.get(k, "") for k in keys))
s = d["statistics"]
print("\nrecordsScanned=%d recordsMatched=%d bytesScanned=%d" % (s["recordsScanned"], s["recordsMatched"], s["bytesScanned"]))
PYEOF
rm -f "$RESULT"
