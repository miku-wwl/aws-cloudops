"""第 13 讲实验 13-1 测试：python -m unittest -v"""
import json
import unittest
from datetime import datetime, timedelta

import canon
import recovery as r


class Timing(unittest.TestCase):
    def test_textbook_example(self):
        self.assertEqual(r.minutes(r.t("10:00"), r.t("10:20")), 20)
        self.assertEqual(r.minutes(r.t("10:20"), r.t("11:05")), 45)

    def test_last_recovery_point(self):
        rp = r.last_recovery_point(datetime(2026, 11, 17, 14, 30), datetime(2026, 11, 1, 5, 0), timedelta(days=1))
        self.assertEqual(rp, datetime(2026, 11, 17, 5, 0))           # 丢 9.5 小时


class Canonical(unittest.TestCase):
    def setUp(self):
        self.base = canon.load("sample-baseline.json")
        self.restored = canon.load("sample-restored.json")
        self.source = canon.load("sample-source-now.json")

    def test_order_and_number_format_do_not_matter(self):
        self.assertEqual(canon.digest(self.base), canon.digest(self.restored))

    def test_textbook_numbers(self):
        s = canon.summary(self.base)
        self.assertEqual((s["count"], s["amount_sum"]), (4, 350))
        self.assertEqual(canon.summary(self.source)["amount_sum"], 425)

    def test_source_now_is_not_the_baseline(self):
        self.assertNotEqual(canon.digest(self.base), canon.digest(self.source))

    def test_a_changed_value_is_detected(self):
        changed = json.loads(json.dumps(self.restored))
        changed[0]["status"]["S"] = "PAID"                          # ORDER#003 从 PENDING 变 PAID
        self.assertNotEqual(canon.digest(self.base), canon.digest(changed))


if __name__ == "__main__":
    unittest.main()
