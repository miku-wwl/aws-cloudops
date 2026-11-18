"""python -m unittest -v"""
import unittest

import alarmsim as a


class AlarmSim(unittest.TestCase):
    def test_reproduces_all_official_outcomes(self):
        for seq, m, n, want in a.OFFICIAL:
            for t, exp in want.items():
                got = a.evaluate(a.parse(seq), m, n, t, current="KEEP")
                self.assertEqual(got, "KEEP" if exp == "retain" else exp, f"{seq} M={m} N={n} {t}")

    def test_m_of_n_does_not_need_consecutive(self):
        self.assertEqual(a.evaluate(a.parse("X 0 X"), 2, 3), a.ALARM)
        self.assertEqual(a.evaluate(a.parse("0 0 X"), 2, 3), a.OK)

    def test_premature_rule_waits_for_more_data(self):
        # 文档：'- - - - X' 与 '- - - X -'（M=3）不应立即告警
        self.assertNotEqual(a.evaluate(a.parse("- - - - X"), 3, 3, "missing"), a.ALARM)
        self.assertNotEqual(a.evaluate(a.parse("- - - X -"), 3, 3, "missing"), a.ALARM)


if __name__ == "__main__":
    unittest.main()
