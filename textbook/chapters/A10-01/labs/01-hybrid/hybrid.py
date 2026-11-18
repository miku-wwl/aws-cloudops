#!/usr/bin/env python3
"""hybrid：TGW / VPN / Resolver 的往返推理模型（第 17 讲实验 17-1，离线、零费用）。

    python hybrid.py scenarios.json            # 跑全部场景
    python hybrid.py scenarios.json S3 --trace # 只跑一个场景并打印逐跳过程

模型只做“控制面推理”，不发包、不跑 BGP、不查 DNS。它实现的规则全部来自官方文档：
  - VPC 路由表：local 路由优先，其余最长前缀匹配。
  - TGW 路由表：先最长前缀；同一前缀时 静态 > 系统(1:1 NAT) > 前缀列表 > VPC 传播
    > DX 网关传播 > Connect 传播 > 经 DX 的 VPN 传播 > VPN 传播 > ……；blackhole 直接丢弃。
  - 附件“关联”决定进入 TGW 后查哪张表；“传播”决定前缀装进哪些表（可以多张）。
  - 只有源子网所在 AZ 有 TGW 附件子网，流量才能进入 TGW（两个方向都适用）。
  - Resolver 规则按最长域名匹配；同一域名上转发规则优先于自动定义的规则。
"""
from __future__ import annotations

import argparse
import copy
import ipaddress
import json
import sys
import unicodedata
from pathlib import Path

# 同一前缀时的优先级（数字越小越优先），顺序取自 TGW 文档 “Route evaluation order”
PRIORITY = {"static": 0, "system": 1, "prefix-list": 2, "vpc": 3, "dxgw": 4, "connect": 5,
            "vpn-over-dx": 6, "vpn": 7, "vpn-concentrator": 8, "client-vpn": 9, "peering": 10}


def ip(x):
    return ipaddress.ip_address(x)


def net(x):
    return ipaddress.ip_network(x)


def lpm(routes, dst):
    """routes: [(cidr, target, kind)]，返回最优的一条或 None。"""
    cands = [r for r in routes if ip(dst) in net(r[0])]
    if not cands:
        return None
    return min(cands, key=lambda r: (-net(r[0]).prefixlen, PRIORITY.get(r[2], 99)))


def tgw_table(sc, rt):
    """一张 TGW 路由表的实际内容 = 静态路由 + 各附件传播进来的前缀（同前缀时静态覆盖传播）。"""
    t = sc["tgw"]
    routes = [(c, tg, "static") for c, tg in t["route_tables"][rt].get("static", [])]
    for name, a in t["attachments"].items():
        if rt in a.get("propagates_to", []):
            routes += [(c, name, a["type"]) for c in a["prefixes"]]
    return routes


def find_subnet(sc, addr):
    for vname, v in sc["vpcs"].items():
        for sname, s in v["subnets"].items():
            if ip(addr) in net(s["cidr"]):
                return vname, sname, s
    return None


def vpc_attachment(sc, vname):
    return next((n for n, a in sc["tgw"]["attachments"].items() if a.get("vpc") == vname), None)


class Trace:
    def __init__(self):
        self.hops, self.ok, self.why = [], True, ""

    def step(self, ok, text):
        self.hops.append(("  ✓ " if ok else "  ✗ ") + text)
        if not ok and self.ok:
            self.ok, self.why = False, text
        return ok


def leg(sc, src, dst, tr, label):
    """单向：从 src 出发把包送到 dst 所在位置。返回是否送达。"""
    s = find_subnet(sc, src)
    if s:                                             # 源在某个 VPC 里
        vname, sname, sub = s
        v = sc["vpcs"][vname]
        if ip(dst) in net(v["cidr"]):
            return tr.step(True, f"{label}：{dst} 在本 VPC 内，local 路由直接送达")
        r = lpm([(c, tg, "vpc") for c, tg in v["route_tables"][sub["rt"]]], dst)
        if not r or r[1] != "tgw":
            return tr.step(False, f"{label}：子网 {sname} 的路由表没有把 {dst} 指向 TGW")
        att = vpc_attachment(sc, vname)
        a = sc["tgw"]["attachments"].get(att, {})
        if sub["az"] not in a.get("azs", []):
            return tr.step(False, f"{label}：{sname} 所在 {sub['az']} 没有 TGW 附件子网，进不了 TGW")
        tr.step(True, f"{label}：{sname} 路由表 {r[0]} → TGW（附件 {att}）")
    else:                                             # 源在本地机房
        r = lpm([(c, tg, "static") for c, tg in sc["onprem"]["routes"]], dst)
        if not r or r[1] != "vpn":
            return tr.step(False, f"{label}：本地路由表没有到 {dst} 的路由（不会送进 VPN）")
        att = sc["onprem"]["attachment"]
        tr.step(True, f"{label}：本地路由 {r[0]} → VPN（附件 {att}）")
    a = sc["tgw"]["attachments"][att]
    rt = a.get("associated")
    if not rt:
        return tr.step(False, f"{label}：附件 {att} 没有关联任何 TGW 路由表")
    best = lpm(tgw_table(sc, rt), dst)
    if not best:
        return tr.step(False, f"{label}：TGW 表 {rt} 中没有匹配 {dst} 的路由")
    if best[1] == "blackhole":
        return tr.step(False, f"{label}：TGW 表 {rt} 命中 {best[0]} → blackhole（被丢弃）")
    tr.step(True, f"{label}：TGW 表 {rt} 命中 {best[0]} → {best[1]}（{best[2]}）")
    target = sc["tgw"]["attachments"][best[1]]
    if target["type"] == "vpc":
        return tr.step(ip(dst) in net(sc["vpcs"][target["vpc"]]["cidr"]),
                       f"{label}：进入 {target['vpc']}，由 VPC local 路由送达 {dst}")
    in_onprem = any(ip(dst) in net(c) for c in sc["onprem"]["networks"])
    return tr.step(in_onprem, f"{label}：经 {best[1]} 到达本地网络，{dst} 在本地网段内")


def tcp(sc, src, dst, port):
    tr = Trace()
    if leg(sc, src, dst, tr, "去程"):
        if (dst, port) in {(h, p) for h, p in sc.get("listeners", [])}:
            tr.step(True, f"服务：{dst}:{port} 在监听，且防火墙放行")
        else:
            tr.step(False, f"服务：{dst}:{port} 没有监听或被防火墙拒绝")
        if tr.ok:
            leg(sc, dst, src, tr, "回程")
    return tr


def dns_rule(sc, qname):
    """最长域名匹配；同一域名上 FORWARD 优先于自动定义（autodefined）规则。"""
    q = qname.rstrip(".").lower()
    best = None
    for r in sc["dns"]["rules"]:
        d = r["domain"].rstrip(".").lower()
        if d == "" or q == d or q.endswith("." + d):
            key = (len(d.split(".")) if d else 0, r["type"] == "FORWARD")
            if best is None or key > best[0]:
                best = (key, r)
    return best[1] if best else None


def dns(sc, qname, vpc_source_ip):
    tr = Trace()
    r = dns_rule(sc, qname)
    if r is None:
        tr.step(False, f"DNS：{qname} 没有命中任何规则")
        return tr, None
    if r["type"] == "FORWARD":
        tr.step(True, f"DNS：{qname} 命中转发规则 {r['domain']} → {r['target']}（经 Outbound 端点）")
        sub = tcp(sc, sc["dns"]["outbound_ip"], r["target"], 53)
        for h in sub.hops:
            tr.hops.append("    " + h.strip())
        if not sub.ok:
            tr.ok, tr.why = False, "DNS 转发路径不通：" + sub.why
            return tr, None
        ans = sc["dns"]["onprem_records"].get(qname)
        tr.step(ans is not None, f"DNS：本地 DNS 应答 {qname} → {ans or 'NXDOMAIN'}")
        return tr, ans
    ans = sc["dns"].get("phz_records", {}).get(qname)
    tr.step(ans is not None, f"DNS：{qname} 命中 {r['domain'] or '.'}（{r['type']}），"
                            f"VPC Resolver 自己解析 → {ans or 'NXDOMAIN'}")
    return tr, ans


def apply_patch(base, patch):
    sc = copy.deepcopy(base)
    for path, value in patch.items():
        cur, keys = sc, path.split("/")
        for k in keys[:-1]:
            cur = cur[k]
        if value is None:
            cur.pop(keys[-1], None)
        else:
            cur[keys[-1]] = value
    return sc


def run_case(base, case):
    sc = apply_patch(base, case.get("patch", {}))
    out = {}
    if "dns" in case:
        dtr, ans = dns(sc, case["dns"], case.get("src"))
        out["dns"] = dtr
    if "tcp" in case:
        src, dst, port = case["tcp"]
        out["tcp"] = tcp(sc, src, dst, port)
    return out


def pad(text, width):
    """按显示宽度补空格（中文占两格），让终端里的列对齐。"""
    w = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)
    return text + " " * max(0, width - w)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenarios")
    ap.add_argument("only", nargs="?")
    ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()
    spec = json.loads(Path(a.scenarios).read_text(encoding="utf-8"))
    for case in spec["cases"]:
        if a.only and case["id"] != a.only:
            continue
        res = run_case(spec["base"], case)
        parts = []
        for k in ("dns", "tcp"):
            if k in res:
                parts.append(f"{k.upper()}={'ok' if res[k].ok else 'FAIL'}")
        print(f"{case['id']:3} {' '.join(parts):17} {case['title']}")
        for k in ("dns", "tcp"):
            if k in res and (a.trace or not res[k].ok):
                if a.trace:
                    print("\n".join(res[k].hops))
                else:
                    print(f"      └ {res[k].why.strip()}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
