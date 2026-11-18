#!/usr/bin/env python3
"""pathcheck：教学用的“可达性分析器”（第 03 讲实验 3-1，离线、零费用）。

    python pathcheck.py scenarios/baseline.json
    python pathcheck.py scenarios/no-ephemeral-out.json --src-port 49152

它按 AWS 的规则逐跳判断一条 TCP/UDP 流能否往返：
  请求：路由表（最长前缀）→ 源 SG 出站 → 源子网 NACL 出站 → 目的子网 NACL 入站 → 目的 SG 入站
  响应：目的子网 NACL 出站（目的端口 = 客户端临时端口）→ 源子网 NACL 入站
SG 有状态：已放行连接的回包自动允许；NACL 无状态：两个方向都要有规则。
同一子网内的流量不经过 NACL。这是概念模型，不涉及前缀列表、中间设备路由等高级规则。
"""
from __future__ import annotations

import argparse
import ipaddress
import json
from dataclasses import dataclass, field


@dataclass
class Verdict:
    ok: bool
    hops: list[str] = field(default_factory=list)

    def add(self, ok: bool, text: str) -> bool:
        self.hops.append(("✓ " if ok else "✗ ") + text)
        if not ok:
            self.ok = False
        return ok


def ip(x: str):
    return ipaddress.ip_address(x)


def net(x: str):
    return ipaddress.ip_network(x)


def route_lookup(routes, dst: str):
    """最长前缀匹配：返回 (前缀, 目标) 或 None。"""
    cands = [(net(c), t) for c, t in routes if ip(dst) in net(c)]
    if not cands:
        return None
    best = max(cands, key=lambda r: r[0].prefixlen)
    return str(best[0]), best[1]


def nacl_eval(rules, proto: str, peer: str, port: int):
    """按规则号从小到大，第一条匹配即生效；都不匹配则命中 * 默认拒绝。"""
    for num, rproto, cidr, lo, hi, action in sorted(rules, key=lambda r: r[0]):
        if rproto not in ("all", proto):
            continue
        if ip(peer) not in net(cidr):
            continue
        if rproto != "all" and not (lo <= port <= hi):
            continue
        return action == "allow", f"规则 #{num} {action.upper()} {rproto}/{lo}-{hi} {cidr}"
    return False, "规则 *（默认 DENY）"


def sg_allows(sg_rules, proto: str, peer: str, port: int):
    for rproto, cidr, lo, hi in sg_rules:
        if rproto in ("all", proto) and ip(peer) in net(cidr) and (rproto == "all" or lo <= port <= hi):
            return True, f"{rproto}/{lo}-{hi} {cidr}"
    return False, "没有匹配的允许规则（SG 只有允许规则）"


def check(model: dict, src_port: int | None = None) -> Verdict:
    f = model["flow"]
    proto, port = f.get("protocol", "tcp"), int(f["port"])
    sport = int(src_port or f.get("src_port", 49152))
    src = model["hosts"][f["src"]]
    dst = model["hosts"].get(f.get("dst", ""), None)
    dst_ip = dst["ip"] if dst else f["dst_ip"]
    s_sub = model["subnets"][src["subnet"]]
    v = Verdict(ok=True)

    # 1) 路由
    r = route_lookup(model["route_tables"][s_sub["route_table"]], dst_ip)
    if r is None:
        v.add(False, f"路由：{s_sub['route_table']} 中没有覆盖 {dst_ip} 的路由 → 无路可走")
        return v
    prefix, target = r
    v.add(True, f"路由：{dst_ip} 最长匹配 {prefix} → {target}")
    if target == "igw" and not src.get("public_ip"):
        v.add(False, "出口：路由指向 IGW，但源实例没有公网 IPv4，IGW 无法为它做地址转换")
        return v

    # 2) 源 SG 出站（有状态）
    sg_ok, why = False, ""
    for sg in src["sg"]:
        sg_ok, why = sg_allows(model["security_groups"][sg]["egress"], proto, dst_ip, port)
        if sg_ok:
            break
    if not v.add(sg_ok, f"源 SG 出站：{why}"):
        return v

    same_subnet = dst is not None and dst["subnet"] == src["subnet"]
    if same_subnet:
        v.hops.append("· 同一子网：不经过 NACL")
    else:
        ok, why = nacl_eval(model["nacls"][s_sub["nacl"]]["outbound"], proto, dst_ip, port)
        if not v.add(ok, f"源子网 NACL 出站（目的端口 {port}）：{why}"):
            return v
    if dst is None:
        v.hops.append(f"· 目的 {dst_ip} 在 VPC 之外，后续路径不在本模型内")
        return v

    d_sub = model["subnets"][dst["subnet"]]
    if not same_subnet:
        ok, why = nacl_eval(model["nacls"][d_sub["nacl"]]["inbound"], proto, src["ip"], port)
        if not v.add(ok, f"目的子网 NACL 入站（目的端口 {port}）：{why}"):
            return v
    sg_ok = False
    for sg in dst["sg"]:
        sg_ok, why = sg_allows(model["security_groups"][sg]["ingress"], proto, src["ip"], port)
        if sg_ok:
            break
    if not v.add(sg_ok, f"目的 SG 入站：{why}"):
        return v
    if not dst.get("listening", True):
        v.add(False, f"应用：{dst_ip}:{port} 没有进程在监听（RST / 连接被拒绝）")
        return v

    # 3) 响应方向：目的端口变成客户端临时端口
    v.hops.append(f"· 响应：{dst_ip}:{port} → {src['ip']}:{sport}（SG 连接跟踪自动放行）")
    if not same_subnet:
        ok, why = nacl_eval(model["nacls"][d_sub["nacl"]]["outbound"], proto, src["ip"], sport)
        if not v.add(ok, f"目的子网 NACL 出站（目的端口 {sport}）：{why}"):
            return v
        ok, why = nacl_eval(model["nacls"][s_sub["nacl"]]["inbound"], proto, dst_ip, sport)
        if not v.add(ok, f"源子网 NACL 入站（目的端口 {sport}）：{why}"):
            return v
    return v


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenario")
    ap.add_argument("--src-port", type=int)
    a = ap.parse_args()
    with open(a.scenario, encoding="utf-8") as fh:
        model = json.load(fh)
    v = check(model, a.src_port)
    f = model["flow"]
    print(f"流：{f['src']} → {f.get('dst', f.get('dst_ip'))} {f.get('protocol', 'tcp')}/{f['port']}")
    for h in v.hops:
        print("  " + h)
    print("结论：" + ("可往返（REACHABLE）" if v.ok else "不可达（BLOCKED）"))


if __name__ == "__main__":
    main()
