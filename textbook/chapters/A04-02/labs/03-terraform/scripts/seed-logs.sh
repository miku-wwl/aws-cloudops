#!/usr/bin/env bash
# 第 09 讲实验 9-4 ①：把 ../data/requests.jsonl 的 16 条样本写入本章日志组（真实 CreateLogStream + PutLogEvents）。
# 用法（在 03-terraform 目录、terraform apply 之后）：./scripts/seed-logs.sh [region]
# 时间戳会平移到“最近 4 分钟”：日志组只保留 1 天，早于保留期或 14 天前的事件会被拒收。
set -euo pipefail
cd "$(dirname "$0")/.." && source scripts/_common.sh
REGION="${1:-us-east-1}"
GROUP="$(terraform output -raw log_group_name)"
RUN_ID="run-$(date -u +%H%M%S)"
STREAM="sample-$RUN_ID"
EVENTS="$(mktemp)"

"$PY" - "$RUN_ID" "$EVENTS" <<'PYEOF'
import json, pathlib, sys, time
run_id, out = sys.argv[1], sys.argv[2]
lines = [l for l in pathlib.Path("../data/requests.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
now = int(time.time() * 1000)
events = []
for i, line in enumerate(lines):                      # 同一批次必须按时间递增
    r = json.loads(line)
    ts = now - (len(lines) - i) * 15_000
    r["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ts / 1000)) + ".000Z"
    r["runId"] = run_id
    events.append({"timestamp": ts, "message": json.dumps(r, separators=(",", ":"))})
pathlib.Path(out).write_text(json.dumps(events), encoding="utf-8")
PYEOF

aws logs create-log-stream --region "$REGION" --log-group-name "$GROUP" --log-stream-name "$STREAM"
echo "rejectedLogEventsInfo（null 表示全部接收）："
aws logs put-log-events --region "$REGION" --log-group-name "$GROUP" --log-stream-name "$STREAM" \
  --log-events "file://$(winpath "$EVENTS")" --query 'rejectedLogEventsInfo' --output json
rm -f "$EVENTS"
echo "已写入：group=$GROUP stream=$STREAM runId=$RUN_ID"
echo "多轮实验时，在查询开头加一行：filter runId = \"$RUN_ID\""
