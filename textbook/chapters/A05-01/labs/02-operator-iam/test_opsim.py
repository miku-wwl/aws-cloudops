"""第 10 讲实验 10-2 测试（离线）：录制的 AWS 判定必须与手推结果一致。python -m unittest -v"""
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class Recorded(unittest.TestCase):
    def test_every_case_matches_the_simulator(self):
        cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))["cases"]
        got = json.loads((HERE / "aws_results.json").read_text(encoding="utf-8"))["results"]
        for c in cases:
            with self.subTest(c["id"]):
                self.assertEqual(got[c["id"]].split()[0], c["expect"])

    def test_policy_has_no_wildcard_send_command_on_all_documents(self):
        pol = json.loads((HERE / "operator-policy.json").read_text(encoding="utf-8"))
        for st in pol["Statement"]:
            if st["Effect"] == "Allow" and "ssm:SendCommand" in str(st["Action"]):
                self.assertNotIn(st["Resource"], ("*", "arn:aws:ssm:*:*:document/*"))


if __name__ == "__main__":
    unittest.main()
