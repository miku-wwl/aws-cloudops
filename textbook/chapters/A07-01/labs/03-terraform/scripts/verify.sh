#!/usr/bin/env bash
# ④ 失败即退出的验收：恢复表必须与“备份前的基线”一致；源表此刻应是 5 条。
set -euo pipefail
cd "$(dirname "$0")/.." && source scripts/_common.sh
TARGET="$(cat state/restored-table.txt)"
aws dynamodb scan --region "$REGION" --table-name "$TARGET" --consistent-read --output json > state/restored.json
aws dynamodb scan --region "$REGION" --table-name "$TABLE" --consistent-read --output json > state/source-now.json
echo "== 恢复表 vs 基线（应全部一致）"; "$PY" "$CANON" state/baseline.json state/restored.json
echo "== 源表现在 vs 基线（应多出 ORDER#005）"; "$PY" "$CANON" state/baseline.json state/source-now.json || true
