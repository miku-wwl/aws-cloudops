"""python -m unittest -v   （在本目录执行）"""
import json
import unittest

import iameval


class IamEval(unittest.TestCase):
    def test_all_scenarios_match_expectations(self):
        with open("scenarios.json", encoding="utf-8") as fh:
            for sc in json.load(fh):
                for res, want in sc["expect"].items():
                    got, why = iameval.evaluate(sc, sc["action"], res)
                    self.assertEqual(got, want, f"{sc['name']} {res}: {why}")

    def test_explicit_deny_beats_allow(self):
        sc = {"identity": [{"Statement": [{"Effect": "Allow", "Action": "s3:*", "Resource": "*"},
                                          {"Effect": "Deny", "Action": "s3:DeleteObject", "Resource": "*"}]}]}
        self.assertEqual(iameval.evaluate(sc, "s3:DeleteObject", "arn:aws:s3:::b/k")[0], "explicitDeny")
        self.assertEqual(iameval.evaluate(sc, "s3:GetObject", "arn:aws:s3:::b/k")[0], "allowed")

    def test_action_match_is_case_insensitive_resource_is_not(self):
        sc = {"identity": [{"Statement": [{"Effect": "Allow", "Action": "S3:getobject", "Resource": "arn:aws:s3:::b/Logs/*"}]}]}
        self.assertEqual(iameval.evaluate(sc, "s3:GetObject", "arn:aws:s3:::b/Logs/x")[0], "allowed")
        self.assertEqual(iameval.evaluate(sc, "s3:GetObject", "arn:aws:s3:::b/logs/x")[0], "implicitDeny")

    def test_scp_without_allow_denies(self):
        sc = {"identity": [{"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}],
              "scps": [{"Statement": [{"Effect": "Allow", "Action": "ec2:*", "Resource": "*"}]}]}
        self.assertEqual(iameval.evaluate(sc, "s3:GetObject", "arn:aws:s3:::b/k")[0], "implicitDeny")


if __name__ == "__main__":
    unittest.main()
