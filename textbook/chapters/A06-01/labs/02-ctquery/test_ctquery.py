"""第 11 讲实验 11-2 测试（离线）：python -m unittest -v"""
import json
import unittest

import ctquery as c

EVENT = {
    "eventTime": "2026-11-16T08:03:00Z", "eventSource": "s3.amazonaws.com", "eventName": "PutBucketTagging",
    "awsRegion": "us-east-1", "sourceIPAddress": "198.51.100.7", "readOnly": False, "eventID": "0f1e2d3c-aaaa",
    "userIdentity": {"type": "AssumedRole", "arn": "arn:aws:sts::123456789012:assumed-role/OpsRole/alice@example.com",
                     "accountId": "123456789012", "accessKeyId": "ASIAABCDEFGHIJKLMNOP",
                     "sessionContext": {"sessionIssuer": {"arn": "arn:aws:iam::123456789012:role/OpsRole"}}},
    "requestParameters": {"bucketName": "a11-lab01-demo", "Tagging": {"TagSet": {"Tag": [{"Key": "Project"}]}}},
    "recipientAccountId": "123456789012",
}


class Redaction(unittest.TestCase):
    def test_nothing_sensitive_survives(self):
        out = json.dumps(c.redact(EVENT, c.identity_names(EVENT)))
        for secret in ("123456789012", "198.51.100.7", "ASIAABCDEFGHIJKLMNOP", "alice@example.com"):
            self.assertNotIn(secret, out)
        self.assertIn("assumed-role/OpsRole/<session>", out)        # 角色名保留：调查需要它

    def test_summary_keeps_investigation_fields(self):
        s = c.summarize(EVENT)
        self.assertEqual((s["eventName"], s["readOnly"], s["identity"], s["errorCode"]),
                         ("PutBucketTagging", False, "AssumedRole", "-"))
        self.assertEqual(s["requestParameters"], "Tagging, bucketName")

    def test_hidden_parameters_are_reported(self):
        ev = dict(EVENT, requestParameters={"isRedacted": True, "reason": "HIDDEN_DUE_TO_SECURITY_REASONS"})
        self.assertIn("HIDDEN_DUE_TO_SECURITY_REASONS", c.summarize(ev)["requestParameters"])


if __name__ == "__main__":
    unittest.main()
