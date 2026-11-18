"""第 15 讲实验 15-1 测试（离线，使用 run.sh 真实生成的计划 JSON）：python -m unittest -v"""
import json
import unittest
from pathlib import Path

import inspect_plan as ip

FX = Path(__file__).resolve().parent / "fixtures"


def rows(name):
    return ip.changes(json.loads((FX / name).read_text(encoding="utf-8")))


class RealPlans(unittest.TestCase):
    def test_moved_is_a_no_op_with_previous_address(self):
        r = rows("01.plan.json")[0]
        self.assertEqual((r["action"], r["previous_address"]), ("no-op", "terraform_data.orders"))

    def test_trigger_change_is_a_replace(self):
        r = rows("02.plan.json")[0]
        self.assertEqual((r["action"], r["reason"]), ("replace", "replace_because_cannot_update"))

    def test_rename_without_moved_destroys(self):
        actions = sorted(r["action"] for r in rows("03.plan.json"))
        self.assertEqual(actions, ["create", "delete"])

    def test_removed_block_forgets(self):
        self.assertEqual(rows("04.plan.json")[0]["action"], "forget")

    def test_sensitive_value_is_in_the_plan_json(self):
        self.assertIn("Example-Not-A-Real-Secret-42", (FX / "05.plan.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
