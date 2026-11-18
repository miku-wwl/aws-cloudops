"""第 18 讲实验 18-1 的单元测试：python -m unittest -v"""
import json
import unittest
from pathlib import Path

from delivery import evaluate, stage

CASES = {c["id"]: c for c in json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))["cases"]}


def verdict(cid):
    return evaluate(CASES[cid])["verdict"]


class Delivery(unittest.TestCase):
    def test_happy_path_and_non_aft_path(self):
        self.assertEqual(verdict("C1"), "可交付")
        r = evaluate(CASES["C9"])
        self.assertEqual(r["verdict"], "可交付")
        self.assertTrue(all(res == "SKIP" for name, res, _ in r["checks"] if name.startswith("AFT") or name.endswith("定制")))

    def test_first_failing_gate_is_reported_in_order(self):
        self.assertEqual(verdict("C2"), "阻塞于「账户存在」")
        self.assertEqual(verdict("C3"), "阻塞于「OU 已注册」")
        self.assertEqual(verdict("C4"), "阻塞于「账户已纳管」")
        self.assertEqual(verdict("C5"), "阻塞于「全局定制」")

    def test_pipeline_success_is_not_acceptance(self):
        self.assertEqual(verdict("C6"), "阻塞于「独立验收」")

    def test_optional_stage_not_run_is_not_failure(self):
        self.assertEqual(verdict("C7"), "可交付")
        self.assertEqual(stage("x", "NOT_RUN", required=False)[1], "SKIP")
        self.assertEqual(stage("x", "NOT_RUN", required=True)[1], "FAIL")

    def test_unknown_is_missing_evidence_not_failure(self):
        self.assertEqual(verdict("C8"), "证据不足于「全局定制」")

    def test_optional_stage_failed_warns_only(self):
        self.assertEqual(verdict("C10"), "可交付（有 WARN）")


if __name__ == "__main__":
    unittest.main()
