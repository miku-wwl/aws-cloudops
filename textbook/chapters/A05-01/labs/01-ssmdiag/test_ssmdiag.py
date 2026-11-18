"""第 10 讲实验 10-1 测试：python -m unittest -v"""
import json
import unittest
from pathlib import Path

import ssmdiag as d

SC = {s["id"]: s for s in json.loads((Path(__file__).resolve().parent / "scenarios.json").read_text(encoding="utf-8"))["scenarios"]}


def run(i):
    return d.diagnose(SC[i])


class FourLayers(unittest.TestCase):
    def test_baseline_is_fully_usable(self):
        r = run("S1")
        self.assertEqual((r["first_failure"], r["ping"]), (None, "Online"))
        self.assertTrue(r["command"].startswith("Success"))

    def test_no_egress_loses_connection_but_runbook_still_works(self):
        r = run("S2")
        self.assertEqual((r["first_failure"], r["ping"]), ("网络", "ConnectionLost"))
        self.assertTrue(r["runbook"].startswith("Success"))          # 控制面与节点无关

    def test_identity_failures_never_register(self):
        for i in ("S3", "S5", "S10"):
            with self.subTest(i):
                r = run(i)
                self.assertEqual(r["first_failure"], "身份")
                self.assertTrue(r["command"].startswith("InvalidInstanceId"))

    def test_dhmc_replaces_instance_profile(self):
        self.assertEqual(run("S4")["ping"], "Online")

    def test_online_is_not_enough(self):
        r = run("S6")                                                  # 只有 ssm 端点：能心跳，收不到命令
        self.assertEqual(r["ping"], "Online")
        self.assertIn("DeliveryTimedOut", r["command"])
        self.assertIn("ssmmessages", r["session"])

    def test_agent_version_decides_message_channel(self):
        self.assertTrue(run("S7")["command"].startswith("Success"))    # 3.3.x 用 ssmmessages
        self.assertIn("ec2messages", run("S8")["command"])             # 3.2.x 仍要 ec2messages

    def test_private_dns_off_makes_endpoints_useless(self):
        self.assertTrue(run("S9")["ping"].startswith("未注册"))

    def test_operator_layer_is_independent_of_node(self):
        r = run("S11")
        self.assertEqual((r["ping"], r["first_failure"]), ("Online", "调用方"))
        self.assertTrue(r["command"].startswith("AccessDenied"))
        self.assertEqual(run("S12")["first_failure"], "调用方")


if __name__ == "__main__":
    unittest.main()
