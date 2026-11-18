#!/usr/bin/env python3
"""ssmdiag：受管节点“四层前提”推理器（第 10 讲实验 10-1，离线、零费用）。

    python ssmdiag.py scenarios.json            # 逐个场景给出：第一个失败层、PingStatus、命令 / 会话 / Runbook 的预期
    python ssmdiag.py scenarios.json --only S6  # 只看一个场景

四层（任何一层失败，后面的现象都由它决定）：
  1. Agent    装了、在运行、版本多少（3.3.40.0 起优先用 ssmmessages 收命令，旧版用 ec2messages）
  2. 身份     实例配置文件里有 ssm:UpdateInstanceInformation，或启用了默认主机管理配置（DHMC：
              需要 IMDSv2 与 Agent ≥ 3.2.582.0）；两者都要靠 IMDS 拿临时凭证
  3. 网络     能用 443 到达 ssm（注册与心跳）以及消息通道 ssmmessages / ec2messages：
              公网路径 = 默认路由 + 公网 IP（或 NAT）+ 安全组出站 443；
              私网路径 = 接口端点 + 私有 DNS + 端点安全组入站 443
  4. 调用方   操作者自己的 IAM（SendCommand / StartSession），与节点在线与否无关
规则的出处见教材第 10 讲参考资料；这是教学模型，不替代真实排障。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

NEW_CHANNEL = (3, 3, 40, 0)     # 起：消息通道优先 ssmmessages
DHMC_MIN = (3, 2, 582, 0)       # 起：支持默认主机管理配置


def ver(s: str) -> tuple:
    return tuple(int(x) for x in s.split("."))


def reachable(net: dict) -> set[str]:
    """节点经 443 能到达哪些 Systems Manager 端点。"""
    if not net.get("sg_egress_443", False) or not net.get("nacl_ok", True) or not net.get("dns", True):
        return set()
    out = set()
    internet = (net.get("route") == "igw" and net.get("public_ip")) or net.get("route") == "nat"
    if internet:
        out |= {"ssm", "ssmmessages", "ec2messages"}
    if net.get("endpoints") and net.get("endpoint_sg_in_443", True) and net.get("private_dns", True):
        out |= set(net["endpoints"])          # 私有 DNS 关闭时，Agent 解析到的是公网地址，端点用不上
    return out


def identity(node: dict) -> tuple[bool, str]:
    idn, agent = node["identity"], node["agent"]
    if not idn.get("imds", True):
        return False, "IMDS 被关闭：实例配置文件与 DHMC 都拿不到临时凭证"
    if idn.get("profile_update_info"):
        return True, "实例配置文件（含 ssm:UpdateInstanceInformation）"
    if idn.get("dhmc") and idn.get("imdsv2", True) and ver(agent["version"]) >= DHMC_MIN:
        return True, "默认主机管理配置（实例配置文件不含 SSM 权限时才会用到它）"
    if idn.get("dhmc"):
        return False, "启用了 DHMC，但不满足 IMDSv2 或 Agent ≥ 3.2.582.0"
    return False, "没有实例配置文件权限，也没有启用 DHMC"


def diagnose(node: dict) -> dict:
    agent, net, op = node["agent"], node["network"], node.get("operator", {})
    layers = []
    agent_ok = agent.get("installed", True) and agent.get("running", True)
    layers.append(("Agent", agent_ok, f"版本 {agent['version']}" if agent_ok else "未安装或未运行"))
    id_ok, id_why = identity(node)
    layers.append(("身份", id_ok, id_why))
    svcs = reachable(net)
    channel = "ssmmessages" if ver(agent["version"]) >= NEW_CHANNEL else "ec2messages"
    can_register = "ssm" in svcs
    can_command = channel in svcs or (channel == "ssmmessages" and "ec2messages" in svcs)
    can_session = "ssmmessages" in svcs
    net_ok = can_register and can_command and can_session
    missing = sorted({"ssm", "ssmmessages", channel} - svcs)
    layers.append(("网络", net_ok, "可达：" + (", ".join(sorted(svcs)) or "无") + ("；缺：" + ", ".join(missing) if missing else "")))
    labels = {"send_command": "ssm:SendCommand", "start_session": "ssm:StartSession",
              "runbook": "Runbook 内的 ec2:DescribeInstances"}
    denied = [labels[k] for k in labels if not op.get(k, True)]
    layers.append(("调用方", not denied, "IAM 允许" if not denied else "缺少：" + "、".join(denied)))

    running = node.get("ec2_state", "running") == "running"
    online = running and agent_ok and id_ok and can_register
    if online:
        ping = "Online"
    elif node.get("was_online"):
        ping = "ConnectionLost"
    else:
        ping = "未注册（describe-instance-information 查不到）"

    if not op.get("send_command", True):
        command = "AccessDeniedException：API 直接拒绝，没有 CommandId"
    elif ping.startswith("未注册"):
        command = "InvalidInstanceId：节点未注册或 Agent 未运行"
    elif ping == "ConnectionLost":
        command = "收不到：停在 Pending/InProgress 直到超时（DeliveryTimedOut），或显示 Undeliverable"
    elif not can_command:
        command = f"节点 Online 但收不到命令：缺 {channel}，Pending → DeliveryTimedOut"
    else:
        command = "Success（只说明脚本退出码为 0）"

    if not op.get("start_session", True):
        session = "AccessDeniedException"
    elif ping != "Online":
        session = "TargetNotConnected"
    elif not can_session:
        session = "会话建立失败：数据通道需要 ssmmessages"
    else:
        session = "可以建立会话"

    runbook = ("Success：控制面 API，不经过节点" if op.get("runbook", True)
               else "失败：Runbook 的执行身份缺少 ec2:DescribeInstances")
    first = next((name for name, ok, _ in layers if not ok), None)
    return {"layers": layers, "first_failure": first, "ping": ping, "command": command,
            "session": session, "runbook": runbook}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenarios")
    ap.add_argument("--only")
    a = ap.parse_args()
    for sc in json.loads(Path(a.scenarios).read_text(encoding="utf-8"))["scenarios"]:
        if a.only and sc["id"] != a.only:
            continue
        r = diagnose(sc)
        print(f"\n{sc['id']} {sc['title']}")
        print("  " + "  ".join(f"[{'✓' if ok else '✗'}]{name}" for name, ok, _ in r["layers"]),
              f"→ 第一个失败层：{r['first_failure'] or '无'}")
        for name, ok, why in r["layers"]:
            if not ok:
                print(f"    {name}：{why}")
        print(f"  PingStatus：{r['ping']}")
        print(f"  Run Command：{r['command']}")
        print(f"  Session：{r['session']}；Runbook：{r['runbook']}")


if __name__ == "__main__":
    main()
