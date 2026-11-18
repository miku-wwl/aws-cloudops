"""第 14 讲实验 14-1 测试：python -m unittest -v"""
import json
import unittest
from pathlib import Path

import ir

HERE = Path(__file__).resolve().parent
CASE = json.loads((HERE / "case.json").read_text(encoding="utf-8"))
PROBES = [json.loads(l) for l in (HERE / "probes.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


class Diagnosis(unittest.TestCase):
    def test_only_the_sg_hypothesis_survives(self):
        verdicts = {r["id"]: r["verdict"] for r in ir.dx(CASE)}
        self.assertEqual([k for k, v in verdicts.items() if v == "存活"], ["H1"])

    def test_missing_observation_keeps_rivals_alive(self):
        case = json.loads(json.dumps(CASE))
        case["observations"] = [o for o in case["observations"] if o["id"] not in ("O7", "O8")]
        alive = [r["id"] for r in ir.dx(case) if r["verdict"] == "存活"]
        self.assertIn("H4", alive)                      # 没有 O7、O8，NACL 假设无法排除


class Window(unittest.TestCase):
    def test_duration_is_an_interval(self):
        w = ir.window(PROBES)
        self.assertEqual((w["duration_min_lower"], w["duration_min_upper"]), (13.0, 15.0))
        self.assertEqual((w["last_ok"], w["first_ok_after"]), ("2026-11-17T10:06:00Z", "2026-11-17T10:21:00Z"))

    def test_detection_time(self):
        self.assertEqual(ir.window(PROBES, "2026-11-17T10:12:00Z")["detect_min"], 5.0)


if __name__ == "__main__":
    unittest.main()
