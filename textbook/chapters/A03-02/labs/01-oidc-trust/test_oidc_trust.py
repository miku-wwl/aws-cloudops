"""python -m unittest -v"""
import unittest

import oidc_trust as o


class OidcTrust(unittest.TestCase):
    def test_exact_old_format_only_main(self):
        p = o.POLICIES["P1 精确：旧格式 main"]
        self.assertTrue(o.assumable(p, o.TOKENS["T1 main 推送（旧格式）"]))
        self.assertFalse(o.assumable(p, o.TOKENS["T2 feature 分支"]))
        self.assertFalse(o.assumable(p, o.TOKENS["T5 main（新格式，含数字 ID）"]))   # 格式变了就不匹配

    def test_new_format_rejects_recreated_repo(self):
        p = o.POLICIES["P2 精确：新格式 main"]
        self.assertTrue(o.assumable(p, o.TOKENS["T5 main（新格式，含数字 ID）"]))
        self.assertFalse(o.assumable(p, o.TOKENS["T6 同名仓库被他人重建（新格式）"]))

    def test_wildcard_lets_other_repos_in(self):
        self.assertTrue(o.assumable(o.POLICIES["P5 通配 repo:*（危险）"], o.TOKENS["T7 别的仓库"]))

    def test_provider_controls(self):
        self.assertFalse(o.provider_controls_ok(o.POLICIES["P6 没有 sub 条件（会被 IAM 拒绝）"])[0])
        self.assertFalse(o.provider_controls_ok(o.POLICIES["P5 通配 repo:*（危险）"])[0])
        self.assertTrue(o.provider_controls_ok(o.POLICIES["P1 精确：旧格式 main"])[0])


if __name__ == "__main__":
    unittest.main()
