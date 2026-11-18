#!/usr/bin/env python3
"""sgaudit：安全组只读审计 + “多 SG 叠加后的有效权限”计算（第 04 讲实验 4-1）。

    # 审计（输入是 describe-security-groups 的 JSON；不加 --file 时调用 AWS CLI 只读获取）
    aws ec2 describe-security-groups --output json > sgs.json
    python sgaudit.py audit --file sgs.json
    # 有效权限：一块网卡挂了多个 SG 时，某个来源能否访问某个端口
    python sgaudit.py allow --file fixtures/three-tier.json --sg sg-app --sg sg-extra \
        --proto tcp --port 8080 --source-sg sg-web

规则依据（AWS 文档）：SG 只有允许规则；同一网卡上多个 SG 的规则取并集；
引用 SG 的规则匹配“挂了该 SG 的网卡的私有 IP”；无入站规则 = 拒绝一切入站。
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import subprocess
import sys

ADMIN_PORTS = {22: "SSH", 3389: "RDP", 3306: "MySQL", 5432: "PostgreSQL", 1433: "SQL Server",
               6379: "Redis", 9200: "OpenSearch", 27017: "MongoDB", 2375: "Docker API"}
WORLD = {"0.0.0.0/0", "::/0"}


def load(path: str | None) -> list[dict]:
    if path:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        out = subprocess.run(["aws", "ec2", "describe-security-groups", "--output", "json"],
                             check=True, capture_output=True, text=True).stdout
        data = json.loads(out)
    return data["SecurityGroups"] if isinstance(data, dict) else data


def sources(perm: dict) -> list[tuple[str, str]]:
    """把一条权限展开成 (类型, 值) 列表。"""
    s = [("cidr", r["CidrIp"]) for r in perm.get("IpRanges", [])]
    s += [("cidr", r["CidrIpv6"]) for r in perm.get("Ipv6Ranges", [])]
    s += [("sg", r["GroupId"]) for r in perm.get("UserIdGroupPairs", [])]
    s += [("pl", r["PrefixListId"]) for r in perm.get("PrefixListIds", [])]
    return s


def port_range(perm: dict) -> tuple[int, int]:
    if perm.get("IpProtocol") == "-1":
        return 0, 65535
    return perm.get("FromPort", 0), perm.get("ToPort", 65535)


def proto_name(p: str) -> str:
    return {"-1": "all", "6": "tcp", "17": "udp", "1": "icmp"}.get(p, p)


def audit(sgs: list[dict]) -> list[str]:
    findings = []
    ids = {g["GroupId"] for g in sgs}
    for g in sgs:
        gid, name = g["GroupId"], g.get("GroupName", "")
        ingress_all_world = egress_all_world = False
        for perm in g.get("IpPermissions", []):
            lo, hi = port_range(perm)
            proto = proto_name(perm.get("IpProtocol", ""))
            for kind, val in sources(perm):
                if kind == "cidr" and val in WORLD:
                    if proto == "all":
                        ingress_all_world = True
                        findings.append(f"HIGH  {gid}({name}) 入站对 {val} 开放全部流量")
                    else:
                        for p, svc in ADMIN_PORTS.items():
                            if lo <= p <= hi:
                                findings.append(f"HIGH  {gid}({name}) 入站对 {val} 开放 {svc} {proto}/{p}")
                        if hi - lo >= 1000:
                            findings.append(f"MED   {gid}({name}) 入站对 {val} 开放大端口段 {proto}/{lo}-{hi}")
                        if lo == 0 and hi == 65535 and proto in ("tcp", "udp"):
                            ingress_all_world = True
                if kind == "sg" and val not in ids:
                    findings.append(f"MED   {gid}({name}) 引用了不存在或其他账户的 SG {val}（可能已失效 / stale）")
                if kind == "sg" and val == gid and proto == "all":
                    findings.append(f"INFO  {gid}({name}) 自引用：挂了本 SG 的网卡彼此之间全部放行")
        for perm in g.get("IpPermissionsEgress", []):
            for kind, val in sources(perm):
                if kind == "cidr" and val in WORLD and port_range(perm) == (0, 65535):
                    egress_all_world = True
                    findings.append(f"INFO  {gid}({name}) 出站允许全部流量到 {val}（AWS 新建 SG 的默认值）")
        if ingress_all_world and egress_all_world:
            findings.append(f"MED   {gid}({name}) 入站与出站都对全网开放 TCP/UDP 全端口：这类流不被连接跟踪，删除规则会立即中断现有连接")
        if not g.get("IpPermissions"):
            findings.append(f"INFO  {gid}({name}) 没有入站规则：拒绝一切新的入站连接")
    return findings


def allows(sgs: list[dict], attached: list[str], proto: str, port: int,
           source_ip: str | None, source_sgs: list[str]) -> tuple[bool, str]:
    """一块网卡挂了 attached 这些 SG；来源为 source_ip 或挂了 source_sgs 的网卡，判断入站是否放行。"""
    by_id = {g["GroupId"]: g for g in sgs}
    for gid in attached:
        for perm in by_id[gid].get("IpPermissions", []):
            pp = proto_name(perm.get("IpProtocol", ""))
            lo, hi = port_range(perm)
            if pp not in ("all", proto) or not (lo <= port <= hi):
                continue
            for kind, val in sources(perm):
                if kind == "cidr" and source_ip and ipaddress.ip_address(source_ip) in ipaddress.ip_network(val):
                    return True, f"{gid} 的规则 {pp}/{lo}-{hi} 来自 {val}"
                if kind == "sg" and val in source_sgs:
                    return True, f"{gid} 的规则 {pp}/{lo}-{hi} 来自 {val}（按网卡私有 IP 匹配）"
    return False, "所有已挂载 SG 的规则并集中都没有匹配的允许规则 → 丢弃（SG 没有显式拒绝）"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("audit"); a1.add_argument("--file")
    a2 = sub.add_parser("allow"); a2.add_argument("--file"); a2.add_argument("--sg", action="append", required=True)
    a2.add_argument("--proto", default="tcp"); a2.add_argument("--port", type=int, required=True)
    a2.add_argument("--source-ip"); a2.add_argument("--source-sg", action="append", default=[])
    a = ap.parse_args()
    sgs = load(a.file)
    if a.cmd == "audit":
        f = audit(sgs)
        print(f"共 {len(sgs)} 个安全组，{len(f)} 条发现")
        for line in f:
            print("  " + line)
        sys.exit(1 if any(x.startswith("HIGH") for x in f) else 0)
    ok, why = allows(sgs, a.sg, a.proto, a.port, a.source_ip, a.source_sg)
    print(("允许  " if ok else "拒绝  ") + why)


if __name__ == "__main__":
    main()
