"""第 09 讲实验 9-2 测试：python -m unittest -v（离线，对照已录制的 AWS 实测结果）"""
import json
import unittest
from pathlib import Path

import patterns as p

RECORDED = json.loads((Path(__file__).resolve().parent / "aws_results.json").read_text(encoding="utf-8"))["results"]


class AgainstAws(unittest.TestCase):
    def test_every_case_agrees_with_test_event_pattern(self):
        for cid, title, pattern, event in p.load_cases():
            with self.subTest(cid=cid, title=title):
                self.assertEqual(p.match(pattern, event), RECORDED[cid])


class LocalRules(unittest.TestCase):
    EVENT = {"source": "cloudops.lab", "detail": {"file": "dir/a*.png", "n": 7}}

    def test_wildcard_escape(self):
        self.assertTrue(p.match({"detail": {"file": [{"wildcard": "dir/a\*.png"}]}}, self.EVENT))
        self.assertFalse(p.match({"detail": {"file": [{"wildcard": "dir/b\*.png"}]}}, self.EVENT))

    def test_numeric_closed_range(self):
        self.assertTrue(p.match({"detail": {"n": [{"numeric": [">", 5, "<=", 7]}]}}, self.EVENT))
        self.assertFalse(p.match({"detail": {"n": [{"numeric": [">", 7]}]}}, self.EVENT))

    def test_anything_but_prefix(self):
        self.assertFalse(p.match({"source": [{"anything-but": {"prefix": "cloudops."}}]}, self.EVENT))


if __name__ == "__main__":
    unittest.main()
