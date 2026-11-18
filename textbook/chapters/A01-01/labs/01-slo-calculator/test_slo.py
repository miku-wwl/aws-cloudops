"""python -m unittest -v   （在本目录执行）"""
import unittest

import slo


class SloMath(unittest.TestCase):
    def test_function_layer_sli(self):
        self.assertAlmostEqual(slo.request_sli(1000, 2), 0.998)

    def test_user_view_with_throttles(self):
        # 例题 2-1：1000 次执行 + 3 次限流 = 1003 个请求，失败 5 个
        self.assertAlmostEqual(slo.request_sli(1003, 5), 0.995015, places=6)

    def test_zero_requests_has_no_sli(self):
        with self.assertRaises(ValueError):
            slo.request_sli(0, 0)

    def test_period_budget_30_days(self):
        self.assertAlmostEqual(slo.period_budget_minutes(30, 0.999), 43.2)

    def test_burn_thresholds_from_aws_docs(self):
        # AWS 文档示例：30 天区间、1 小时窗口内消耗 5% 预算 → 36
        self.assertAlmostEqual(slo.burn_threshold(0.05, 720, 1), 36)
        # 本章采用：1h 内耗 2% → 14.4；6h 内耗 5% → 6
        self.assertAlmostEqual(slo.burn_threshold(0.02, 720, 1), 14.4)
        self.assertAlmostEqual(slo.burn_threshold(0.05, 720, 6), 6)

    def test_error_ratio_threshold(self):
        self.assertAlmostEqual(slo.error_ratio_threshold(14.4, 0.999), 0.0144)
        self.assertAlmostEqual(slo.burn_rate(0.0144, 0.999), 14.4)

    def test_exhaustion_time(self):
        self.assertAlmostEqual(slo.hours_to_exhaustion(14.4, 720), 50)

    def test_pct_normalisation(self):
        self.assertAlmostEqual(slo.pct(99.9), 0.999)
        self.assertAlmostEqual(slo.pct(0.999), 0.999)


if __name__ == "__main__":
    unittest.main()
