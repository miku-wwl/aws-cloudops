"""第 11 讲实验 11-3 测试（离线）"""
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class Recorded(unittest.TestCase):
    def test_guardrail_decisions(self):
        spec = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
        got = json.loads((HERE / "aws_results.json").read_text(encoding="utf-8"))["results"]
        for c in spec["cases"]:
            with self.subTest(c["id"]):
                self.assertEqual(got[c["id"]], c["expect"])


if __name__ == "__main__":
    unittest.main()
