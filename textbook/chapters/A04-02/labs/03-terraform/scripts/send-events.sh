#!/usr/bin/env bash
# 9-4 ③：向自定义总线发布 3 条事件（真实 PutEvents）：两条负例 + 一条正例。
# 用法：./scripts/send-events.sh [region] [errorRate，默认 75]
set -euo pipefail
cd "$(dirname "$0")/.." && source scripts/_common.sh
REGION="${1:-us-east-1}"
RATE="${2:-75}"
BUS="$(terraform output -raw event_bus_name)"
ENTRIES="$(mktemp)"

"$PY" - "$BUS" "$RATE" "$ENTRIES" <<'PYEOF'
import json, sys
bus, rate, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
rate = int(rate) if rate.is_integer() else rate
def entry(source, severity, note):
    detail = {"service": "checkout", "release": "v2.3.1", "phase": "canary",
              "severity": severity, "errorRate": rate, "note": note}
    return {"EventBusName": bus, "Source": source, "DetailType": "DeploymentAnomaly",
            "Detail": json.dumps(detail, ensure_ascii=False)}
entries = [entry("cloudops.other", "high", "负例1：source 不同"),
           entry("cloudops.lab", "HIGH", "负例2：大小写不同"),
           entry("cloudops.lab", "high", "正例")]
open(out, "w", encoding="utf-8").write(json.dumps(entries, ensure_ascii=False))
PYEOF

aws events put-events --region "$REGION" --entries "file://$(winpath "$ENTRIES")" \
  --query '{FailedEntryCount: FailedEntryCount, EventIds: Entries[].EventId}' --output json
rm -f "$ENTRIES"
echo "三条都拿到 EventId 只说明“总线收下了”；只有第 3 条命中规则。到队列里验证：./scripts/receive.sh $REGION"
