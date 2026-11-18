"""第 12 讲实验 12-1 测试：python -m unittest -v"""
import copy
import json
import unittest
from pathlib import Path

import twogates as g

SC = {s["id"]: s for s in json.loads((Path(__file__).resolve().parent / "scenarios.json").read_text(encoding="utf-8"))["scenarios"]}
R = {k: g.evaluate(v)["result"] for k, v in SC.items()}


class TwoGates(unittest.TestCase):
    def test_happy_paths(self):
        for i in ("T1", "T4"):
            self.assertEqual(R[i], "成功", i)

    def test_s3_gate_failures(self):
        for i in ("T2", "T6", "T7"):
            self.assertEqual(R[i], "AccessDenied（S3 门）", i)

    def test_kms_gate_failures(self):
        for i in ("T3", "T5", "T8", "T9"):
            self.assertEqual(R[i], "AccessDenied（KMS 门）", i)

    def test_encryption_type_decides_whether_kms_is_involved(self):
        self.assertEqual(R["T10"], "成功")                    # 同一个 auditor，读 SSE-S3 对象成功

    def test_multipart_succeeds_once_decrypt_is_added(self):
        sc = copy.deepcopy(SC["T5"])
        sc["principal"]["kms_actions"].append("kms:Decrypt")
        self.assertEqual(g.evaluate(sc)["result"], "成功")


if __name__ == "__main__":
    unittest.main()
