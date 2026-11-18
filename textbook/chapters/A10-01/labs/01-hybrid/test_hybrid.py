"""第 17 讲实验 17-1 的单元测试：python -m unittest -v"""
import json
import unittest
from pathlib import Path

import hybrid

SPEC = json.loads((Path(__file__).parent / "scenarios.json").read_text(encoding="utf-8"))
CASES = {c["id"]: c for c in SPEC["cases"]}


def run(cid):
    return hybrid.run_case(SPEC["base"], CASES[cid])


class RouteTables(unittest.TestCase):
    def test_baseline_and_inbound_dns_pass(self):
        for cid in ("S1", "S12"):
            r = run(cid)
            self.assertTrue(all(t.ok for t in r.values()), cid)

    def test_longest_prefix_beats_shorter_even_if_blackhole(self):
        r = run("S4")["tcp"]
        self.assertFalse(r.ok)
        self.assertIn("172.16.20.0/24 → blackhole", r.why)

    def test_same_prefix_priority_static_then_dx_then_vpn(self):
        self.assertIn("att-dx（dxgw）", "\n".join(run("S7")["tcp"].hops))
        self.assertIn("att-vpn（static）", "\n".join(run("S8")["tcp"].hops))

    def test_return_path_is_a_separate_lookup(self):
        r = run("S3")["tcp"]
        self.assertFalse(r.ok)
        self.assertTrue(r.why.startswith("回程"))

    def test_association_and_attachment_az(self):
        self.assertIn("TGW 表 hybrid 中没有匹配", run("S5")["tcp"].why)
        self.assertIn("没有 TGW 附件子网", run("S6")["tcp"].why)

    def test_spoke_isolation_and_default_table_breaks_it(self):
        self.assertFalse(run("S2")["tcp"].ok)
        self.assertTrue(run("S9")["tcp"].ok)


class Resolver(unittest.TestCase):
    def test_dns_and_tcp_fail_independently(self):
        for cid in ("S10", "S11"):
            r = run(cid)
            self.assertFalse(r["dns"].ok, cid)
            self.assertTrue(r["tcp"].ok, cid)

    def test_most_specific_domain_and_forward_wins_tie(self):
        sc = {"dns": {"rules": [
            {"domain": "corp.example", "type": "FORWARD", "target": "172.16.0.53"},
            {"domain": "internal.corp.example", "type": "SYSTEM", "target": "PHZ"},
            {"domain": "aws.example", "type": "SYSTEM", "target": "PHZ", "autodefined": True},
            {"domain": "aws.example", "type": "FORWARD", "target": "172.16.0.53"},
            {"domain": "", "type": "RECURSIVE", "target": "Internet Resolver", "autodefined": True}]}}
        self.assertEqual(hybrid.dns_rule(sc, "db.internal.corp.example")["type"], "SYSTEM")
        self.assertEqual(hybrid.dns_rule(sc, "db.corp.example")["type"], "FORWARD")
        self.assertEqual(hybrid.dns_rule(sc, "x.aws.example")["type"], "FORWARD")
        self.assertEqual(hybrid.dns_rule(sc, "www.example.org")["type"], "RECURSIVE")


if __name__ == "__main__":
    unittest.main()
