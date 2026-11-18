"""第 16 讲实验 16-1 测试：python -m unittest -v"""
import json
import unittest
from pathlib import Path

import pipeline as p

SPEC = json.loads((Path(__file__).resolve().parent / "scenarios.json").read_text(encoding="utf-8"))
STAGE = {d["id"]: p.run(d)["stage"] for d in SPEC["deploys"]}


class FourControls(unittest.TestCase):
    def test_each_control_fails_on_its_own(self):
        self.assertEqual(STAGE, {"D1": "通过", "D2": "审批", "D3": "身份", "D4": "身份", "D5": "权限", "D6": "锁", "D7": "身份"})

    def test_approval_does_not_imply_trust(self):
        self.assertEqual(STAGE["D3"], "身份")            # 已批准，但 sub 字面不一致


class Drift(unittest.TestCase):
    def test_three_routes(self):
        routes = [p.drift_route(d)[:2] for d in SPEC["drifts"]]
        self.assertEqual(routes, ["恢复", "接受", "暂停"])


if __name__ == "__main__":
    unittest.main()
