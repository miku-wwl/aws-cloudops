"""python -m unittest -v   （在本目录执行）"""
import json
import unittest

import pathcheck


def load(name):
    with open(f"scenarios/{name}.json", encoding="utf-8") as fh:
        return json.load(fh)


class PathCheck(unittest.TestCase):
    def test_longest_prefix_wins(self):
        routes = [["10.20.0.0/16", "local"], ["0.0.0.0/0", "nat"]]
        self.assertEqual(pathcheck.route_lookup(routes, "10.20.2.20"), ("10.20.0.0/16", "local"))
        self.assertEqual(pathcheck.route_lookup(routes, "1.1.1.1"), ("0.0.0.0/0", "nat"))

    def test_nacl_first_match_wins(self):
        rules = [[100, "all", "0.0.0.0/0", 0, 65535, "allow"], [90, "tcp", "10.20.1.0/24", 8080, 8080, "deny"]]
        ok, why = pathcheck.nacl_eval(rules, "tcp", "10.20.1.15", 8080)
        self.assertFalse(ok)
        self.assertIn("#90", why)

    def test_baseline_reachable(self):
        self.assertTrue(pathcheck.check(load("baseline")).ok)

    def test_deny_rule_blocks_request(self):
        v = pathcheck.check(load("deny-8080"))
        self.assertFalse(v.ok)
        self.assertIn("#90", v.hops[-1])

    def test_stateless_nacl_blocks_response(self):
        v = pathcheck.check(load("no-ephemeral-out"))
        self.assertFalse(v.ok)
        self.assertIn("49152", v.hops[-1])          # 请求进来了，回包被挡在出站方向

    def test_ephemeral_rule_fixes_response(self):
        self.assertTrue(pathcheck.check(load("strict-fixed")).ok)

    def test_private_subnet_has_no_route_to_internet(self):
        v = pathcheck.check(load("private-to-internet"))
        self.assertFalse(v.ok)
        self.assertIn("没有覆盖", v.hops[-1])

    def test_igw_needs_public_ip(self):
        v = pathcheck.check(load("public-no-public-ip"))
        self.assertFalse(v.ok)
        self.assertIn("公网 IPv4", v.hops[-1])

    def test_not_listening(self):
        self.assertFalse(pathcheck.check(load("not-listening")).ok)


if __name__ == "__main__":
    unittest.main()
