"""第 11 讲实验 11-1 测试：python -m unittest -v"""
import unittest

import s3tagged as t


class Semantics(unittest.TestCase):
    def test_put_bucket_tagging_replaces_everything(self):
        out = t.put_bucket_tagging(t.BASELINE, {"CostCenter": "cc-42"})
        self.assertEqual(out, {"CostCenter": "cc-42"})

    def test_tag_resource_merges(self):
        out = t.tag_resource(t.BASELINE, {"CostCenter": "cc-42"})
        self.assertEqual(out["Owner"], "cloudops-lab")
        self.assertEqual(len(out), 5)

    def test_untag_resource_removes_only_named_keys(self):
        self.assertNotIn("Owner", t.untag_resource(t.BASELINE, ["Owner"]))
        self.assertEqual(len(t.untag_resource(t.BASELINE, ["Nope"])), 4)


class Rule(unittest.TestCase):
    def test_no_tags_is_noncompliant(self):
        self.assertEqual(t.s3_bucket_tagged({}), "NON_COMPLIANT")

    def test_aws_prefixed_tags_do_not_count(self):
        self.assertEqual(t.s3_bucket_tagged({"aws:cloudformation:stack-name": "x"}), "NON_COMPLIANT")

    def test_required_keys_are_case_sensitive(self):
        self.assertEqual(t.s3_bucket_tagged({"owner": "a"}, "Owner"), "NON_COMPLIANT")
        self.assertEqual(t.s3_bucket_tagged({"Owner": "a", "Env": "b"}, "Owner, Env"), "COMPLIANT")

    def test_timeline_reproduces_the_incident(self):
        states = [t.s3_bucket_tagged(tags, "Owner") for _, _, tags in t.timeline(abac=False)]
        self.assertEqual(states, ["COMPLIANT", "NON_COMPLIANT", "COMPLIANT"])
        states = [t.s3_bucket_tagged(tags, "Owner") for _, _, tags in t.timeline(abac=True)]
        self.assertEqual(states, ["COMPLIANT"] * 3)


if __name__ == "__main__":
    unittest.main()
