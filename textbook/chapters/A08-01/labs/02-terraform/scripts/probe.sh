#!/usr/bin/env bash
# 第 14 讲实验 14-3 ①：外部探针。每次都是“新进程 + 新 TCP 连接”，结果追加到 probes.jsonl。
# 用法：./scripts/probe.sh [次数，默认 1] [间隔秒，默认 60]
set -uo pipefail
cd "$(dirname "$0")/.."
URL="$(terraform output -raw test_url)"; N="${1:-1}"; GAP="${2:-60}"
for i in $(seq 1 "$N"); do
  TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  CODE=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 8 -H 'Connection: close' "$URL"); EXIT=$?
  OK=false; [ "$EXIT" -eq 0 ] && [ "$CODE" = "200" ] && OK=true
  echo "{\"ts\":\"$TS\",\"ok\":$OK,\"http\":\"$CODE\",\"curl_exit\":$EXIT}" | tee -a probes.jsonl
  [ "$i" -lt "$N" ] && sleep "$GAP"
done
# curl 退出码：28 = 超时（包被丢弃或无人应答）；7 = 连接被拒绝（端口无人监听）
