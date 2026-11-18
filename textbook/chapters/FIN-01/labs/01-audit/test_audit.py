"""第 19 讲实验 19-1 的单元测试：python -m unittest -v"""
import json
import unittest
from pathlib import Path

from audit import audit

D = Path(__file__).parent / "cases"


def run(name):
    return audit(json.loads((D / f"{name}.json").read_text(encoding="utf-8")))


class Audit(unittest.TestCase):
    def test_late_posting_is_not_new_usage(self):
        r = run("F2-clean-but-late")
        self.assertTrue(all(c == "PRE_DESTROY" for _, c, _ in r["rows"]))
        self.assertEqual(r["post"], 0)
        self.assertIn("已清理", r["verdict"])

    def test_approved_retention_is_cost_but_not_residual(self):
        r = run("F1-demo")
        self.assertEqual([c for _, c, _ in r["rows"]].count("RETAINED"), 2)
        self.assertGreater(r["post"], 0)
        self.assertIn("已清理", r["verdict"])

    def test_unapproved_resources_are_residual(self):
        r = run("F3-residual")
        self.assertEqual([c for _, c, _ in r["rows"]].count("RESIDUAL"), 2)
        self.assertIn("残留", r["verdict"])

    def test_region_outside_coverage_is_a_gap_not_clean(self):
        self.assertIn("覆盖不足", run("F4-coverage-gap")["verdict"])

    def test_credit_is_adjustment(self):
        r = run("F5-credit")
        self.assertIn("ADJUSTMENT", [c for _, c, _ in r["rows"]])
        self.assertIn("已清理", r["verdict"])

    def test_unexplained_usage_points_to_other_state(self):
        self.assertIn("其他 State", run("F6-unexplained")["verdict"])


if __name__ == "__main__":
    unittest.main()
