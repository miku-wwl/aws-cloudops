"""python -m unittest -v"""
import unittest

import envelope as e


class Envelope(unittest.TestCase):
    def setUp(self):
        self.kms = e.FakeKMS()
        self.sm = e.SecretStore(self.kms, "arn:aws:secretsmanager:us-east-1:111122223333:secret:x")
        self.sm.put("v1", "s3cr3t")
        self.sm.readers.add("r")

    def test_needs_both_permissions(self):
        with self.assertRaises(e.AccessDenied):
            self.sm.get("r", "v1")                 # 只有 GetSecretValue
        self.kms.allowed_decrypt.add("r")
        self.assertEqual(self.sm.get("r", "v1"), "s3cr3t")

    def test_context_is_bound(self):
        self.kms.allowed_decrypt.add("r")
        with self.assertRaises(ValueError):
            self.sm.get("r", "v1", tamper_ctx=True)

    def test_store_never_holds_plaintext(self):
        ct, enc_dk = self.sm.versions["v1"]
        self.assertNotIn(b"s3cr3t", ct + enc_dk)

    def test_each_version_gets_new_data_key(self):
        self.sm.put("v2", "s3cr3t")
        self.assertNotEqual(self.sm.versions["v1"][1], self.sm.versions["v2"][1])


if __name__ == "__main__":
    unittest.main()
