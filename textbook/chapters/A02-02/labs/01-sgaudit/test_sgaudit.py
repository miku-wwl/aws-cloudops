"""python -m unittest -v   （在本目录执行）"""
import json
import unittest

import sgaudit


def load(name):
    with open(f"fixtures/{name}.json", encoding="utf-8") as fh:
        return json.load(fh)["SecurityGroups"]


class SgAudit(unittest.TestCase):
    def test_union_of_multiple_sgs(self):
        sgs = load("three-tier")
        ok, _ = sgaudit.allows(sgs, ["sg-extra"], "tcp", 8080, None, ["sg-web"])
        self.assertFalse(ok)                       # 单独挂 sg-extra：没有 8080
        ok, why = sgaudit.allows(sgs, ["sg-extra", "sg-app"], "tcp", 8080, None, ["sg-web"])
        self.assertTrue(ok)                        # 加挂 sg-app：并集中有 8080
        self.assertIn("sg-app", why)

    def test_sg_reference_matches_members_not_cidr(self):
        sgs = load("three-tier")
        ok, _ = sgaudit.allows(sgs, ["sg-db"], "tcp", 5432, "10.20.2.30", [])
        self.assertFalse(ok)                       # 只有 IP、没挂 sg-app 的来源不行
        ok, _ = sgaudit.allows(sgs, ["sg-db"], "tcp", 5432, None, ["sg-app"])
        self.assertTrue(ok)

    def test_cidr_rule(self):
        ok, _ = sgaudit.allows(load("three-tier"), ["sg-extra"], "tcp", 9100, "10.20.9.9", [])
        self.assertTrue(ok)

    def test_audit_flags_world_open_admin_port(self):
        f = sgaudit.audit(load("risky"))
        self.assertTrue(any("SSH" in x and x.startswith("HIGH") for x in f))
        self.assertTrue(any("大端口段" in x for x in f))
        self.assertTrue(any("sg-deleted" in x for x in f))
        self.assertTrue(any("不被连接跟踪" in x for x in f))

    def test_clean_three_tier_has_no_high(self):
        self.assertFalse(any(x.startswith("HIGH") for x in sgaudit.audit(load("three-tier"))))


if __name__ == "__main__":
    unittest.main()
