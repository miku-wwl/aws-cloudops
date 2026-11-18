"""第 09 讲实验 9-1 测试：python -m unittest -v

教材里出现的每一条查询都来自 ../queries/*.cwli，这里用同一份文件验证教材中的数字。
"""
import unittest
from pathlib import Path

import insights as q

HERE = Path(__file__).resolve().parent
ROWS = q.load(HERE.parent / "data" / "requests.jsonl")


def query(name):
    return q.run(ROWS, (HERE.parent / "queries" / name).read_text(encoding="utf-8"))


class SavedQueries(unittest.TestCase):
    def test_q1_ingest_check_sees_all_16(self):
        out = query("01-ingest-check.cwli")
        self.assertEqual(len(out), 16)
        self.assertEqual(list(out[0]), ["@timestamp", "requestId", "phase", "release", "route", "status"])

    def test_q2_errors_concentrate_in_one_group(self):
        self.assertEqual(query("02-errors-by-group.cwli"),
                         [{"phase": "canary", "release": "v2", "route": "/checkout", "errors": 6}])

    def test_q3_error_rate_uses_group_denominator(self):
        out = {r["phase"]: r for r in query("03-error-rate.cwli")}
        self.assertEqual((out["canary"]["errors"], out["canary"]["requests"], out["canary"]["errorPct"]), (6, 8, 75.0))
        self.assertEqual(out["baseline"]["errorPct"], 0.0)

    def test_q4_mean_vs_p95(self):
        out = {r["release"]: r for r in query("04-latency.cwli")}
        self.assertAlmostEqual(out["v2"]["avgMs"], 708.125)
        self.assertEqual(out["v2"]["p95Ms"], 930)

    def test_q5_per_minute_buckets(self):
        self.assertEqual([(r["errors"], r["requests"]) for r in query("05-errors-per-minute.cwli")],
                         [(0, 4), (3, 4), (3, 4), (0, 4)])

    def test_q6_canary_by_route(self):
        self.assertEqual({r["route"]: r["errors"] for r in query("06-canary-routes.cwli")}, {"/checkout": 6, "/cart": 0})


class Semantics(unittest.TestCase):
    def test_filtering_first_destroys_the_denominator(self):
        wrong = q.run(ROWS, "filter status >= 500 | stats count(*) as requests, sum(if(status >= 500, 1, 0)) as errors by phase")
        self.assertEqual(wrong, [{"phase": "canary", "requests": 6, "errors": 6}])       # “错误率 100%”是假象

    def test_dividing_by_all_requests_is_wrong_too(self):
        out = q.run(ROWS, "stats 100 * sum(if(status >= 500, 1, 0)) / count(*) as pct")
        self.assertEqual(out[0]["pct"], 37.5)                                             # 6 ÷ 16，不是 75%

    def test_and_binds_tighter_than_or(self):
        out = q.run(ROWS, 'filter phase = "canary" and status = 200 or phase = "baseline" | stats count(*) as n')
        self.assertEqual(out[0]["n"], 2 + 4)

    def test_like_regex_and_in(self):
        self.assertEqual(len(q.run(ROWS, "filter requestId like /req-0[0-3]$/")), 4)
        self.assertEqual(len(q.run(ROWS, 'filter phase in ["canary", "rollback"]')), 12)

    def test_missing_field_never_matches(self):
        self.assertEqual(q.run(ROWS, "filter userId = 'u-1'"), [])
        self.assertEqual(len(q.run(ROWS, "filter not ispresent(userId)")), 16)

    def test_multiple_stats(self):
        out = q.run(ROWS, "stats count(*) as n by phase | stats max(n) as maxN, sum(n) as total")
        self.assertEqual(out, [{"maxN": 8, "total": 16}])

    def test_sort_must_follow_last_stats(self):
        with self.assertRaises(SyntaxError):
            q.run(ROWS, "sort status desc | stats count(*) by phase")

    def test_second_stats_cannot_see_raw_fields(self):
        with self.assertRaises(SyntaxError):
            q.run(ROWS, "stats count(*) as n by phase | stats max(latencyMs)")


if __name__ == "__main__":
    unittest.main()
