#!/usr/bin/env bash
# 10-4 ④：控制变量法的故障注入。只改一项：安全组唯一的出站 443 规则。
# 用法：./scripts/fault.sh off   # 删除出站规则，然后重启实例
#       ./scripts/fault.sh on    # 恢复出站规则
# 为什么要重启：安全组是有状态的，删除规则不会切断已经被跟踪的长连接（第 04 讲）。
# Agent 与 ssmmessages 之间的控制通道就是这样的长连接；重启后 Agent 必须重新建连，故障才会显现。
set -euo pipefail
cd "$(dirname "$0")/.." && source scripts/_common.sh && need_instance
case "${1:-}" in
  off)
    terraform apply -var create_lab_instance=true -var allow_ssm_egress=false   # 会要求输入 yes 确认
    aws ec2 reboot-instances --region "$REGION" --instance-ids "$ID"
    echo "已删除出站 443 并重启。几分钟后运行 ./scripts/status.sh，PingStatus 应变为 ConnectionLost。"
    ;;
  on)
    terraform apply -var create_lab_instance=true -var allow_ssm_egress=true
    echo "已恢复出站 443。等 PingStatus 回到 Online，再用同一个探针 ./scripts/diag.sh 复测。"
    ;;
  *)
    echo "用法：$0 off|on"; exit 2 ;;
esac
