#!/usr/bin/env python3
"""insights：本地迷你 Logs Insights 引擎（第 09 讲实验 9-1，离线、零费用）。

    python insights.py ../data/requests.jsonl ../queries/03-error-rate.cwli
    python insights.py ../data/requests.jsonl -q 'filter status >= 500 | stats count(*) as errors by release'
    python insights.py ../data/requests.jsonl --all ../queries      # 依次运行目录下全部 .cwli

只实现教材用到的 Logs Insights QL 子集，但语义与官方一致：
  fields / display  选择或计算字段，例如 fields status >= 500 as is5xx
  filter            = != < <= > >=、like /正则/ 或 like "子串"、in [..]、and / or / not
                    函数 if()、ispresent()、coalesce()、strcontains()、tolower()、toupper()、strlen()、
                    abs()、floor()、ceil()、round()、bin(1m)
  stats             count(*)、count(f)、sum、avg、min、max、pct(f, p)、countDistinct
                    聚合结果可以继续做算术：100 * sum(if(status >= 500, 1, 0)) / count(*)
                    by 字段或 bin(1m)，可起别名；允许多个 stats（后一个只能引用前一个的输出列）
  sort f asc|desc、limit n      必须写在最后一个 stats 之后（官方规则）
管道左侧的输出就是右侧的输入——这是 Logs Insights 最核心的心智模型。

与真实服务的已知差异（教学简化）：pct 在 CloudWatch 中是近似算法，这里用最近秩法；
字段类型不做自动转换（数字与字符串比较一律为假）；不支持 parse、dedup、pattern 等命令。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path

KEYWORDS = {"and", "or", "not", "like", "in", "as", "by", "asc", "desc"}
AGGREGATES = {"count", "sum", "avg", "min", "max", "pct", "countdistinct"}
PERIOD = re.compile(r"(\d+)(ms|s|m|h|d)$")
UNIT_MS = {"ms": 1, "s": 1000, "m": 60_000, "h": 3_600_000, "d": 86_400_000}


# --------------------------------------------------------------------------- 词法
def tokenize(text: str) -> list[tuple[str, str, int, int]]:
    """返回 (类型, 值, 起点, 终点)。类型：NUM STR ID KW OP REGEX PERIOD。"""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
        elif c == "#":                                    # 注释到行尾
            while i < n and text[i] != "\n":
                i += 1
        elif c == "/" and out and out[-1][0] == "KW" and out[-1][1] == "like":
            j = i + 1
            while j < n and text[j] != "/":
                j += 2 if text[j] == "\\" else 1
            out.append(("REGEX", text[i + 1:j], i, j + 1))
            i = j + 1
        elif c in "\"'":
            j = i + 1
            while j < n and text[j] != c:
                j += 2 if text[j] == "\\" else 1
            out.append(("STR", text[i + 1:j], i, j + 1))
            i = j + 1
        elif c == "`":
            j = text.index("`", i + 1)
            out.append(("ID", text[i + 1:j], i, j + 1))
            i = j + 1
        elif c.isdigit():
            m = re.compile(r"\d+(?:\.\d+)?(?:ms|s|m|h|d)?(?![\w.])").match(text, i)
            if not m:
                raise SyntaxError(f"无法识别的数字：{text[i:i + 10]}")
            v = m.group(0)
            out.append(("PERIOD" if PERIOD.match(v) else "NUM", v, i, m.end()))
            i = m.end()
        elif text.startswith((">=", "<=", "!="), i):
            out.append(("OP", text[i:i + 2], i, i + 2))
            i += 2
        elif c in "=<>+-*/%(),[]|":
            out.append(("OP", c, i, i + 1))
            i += 1
        elif c.isalpha() or c in "@_":
            m = re.compile(r"[@A-Za-z_][\w.@]*").match(text, i)
            v = m.group(0)
            out.append(("KW" if v.lower() in KEYWORDS else "ID", v.lower() if v.lower() in KEYWORDS else v, i, m.end()))
            i = m.end()
        else:
            raise SyntaxError(f"无法识别的字符：{c!r}")
    return out


# --------------------------------------------------------------------------- 语法：编译成闭包
def _cmp(op):
    def f(a, b):
        if a is None or b is None:
            return False                                  # 缺失字段参与比较 → 假
        num = (int, float)
        if isinstance(a, num) != isinstance(b, num):
            return False                                  # 简化：数字与字符串不互相转换
        return {"=": a == b, "!=": a != b, "<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]
    return f


def _arith(op):
    def f(a, b):
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            return None
        if op == "/":
            return None if b == 0 else a / b
        return {"+": a + b, "-": a - b, "*": a * b, "%": a % b if b else None}[op]
    return f


def _fmt_ts(ms) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S.000")


def _bin(period: str):
    m = PERIOD.match(period)
    step = int(m.group(1)) * UNIT_MS[m.group(2)]
    return lambda r: None if r.get("@timestamp") is None else _fmt_ts(r["@timestamp"] // step * step)


ROW_FUNCS = {
    "ispresent": lambda v: v is not None,
    "coalesce": lambda *vs: next((v for v in vs if v is not None), None),
    "strcontains": lambda s, sub: int(sub in s) if isinstance(s, str) else 0,
    "tolower": lambda s: s.lower() if isinstance(s, str) else None,
    "toupper": lambda s: s.upper() if isinstance(s, str) else None,
    "strlen": lambda s: len(s) if isinstance(s, str) else None,
    "abs": lambda v: abs(v) if isinstance(v, (int, float)) else None,
    "floor": lambda v: math.floor(v) if isinstance(v, (int, float)) else None,
    "ceil": lambda v: math.ceil(v) if isinstance(v, (int, float)) else None,
    "round": lambda v, d=0: (round(v, int(d)) if d else round(v)) if isinstance(v, (int, float)) else None,
}


def _numbers(vals):
    return [v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)]


def _aggregate(name: str, args, rows: list[dict]):
    if name == "count":
        if args == "*":
            return len(rows)
        return sum(1 for r in rows if args[0](r) is not None)
    vals = [args[0](r) for r in rows]
    if name == "countdistinct":
        return len({v for v in vals if v is not None})
    nums = _numbers(vals)
    if not nums:
        return None
    if name == "sum":
        return sum(nums)
    if name == "avg":
        return sum(nums) / len(nums)
    if name == "min":
        return min(nums)
    if name == "max":
        return max(nums)
    if name == "pct":                                     # 最近秩法；CloudWatch 用近似算法
        p = args[1]({})
        s = sorted(nums)
        return s[max(0, math.ceil(p / 100 * len(s)) - 1)]
    raise SyntaxError(name)


class Parser:
    """递归下降。agg=True 时，闭包的参数是“一组行”；否则是“一行”。"""

    def __init__(self, toks, text, agg=False):
        self.t, self.text, self.i, self.agg = toks, text, 0, agg
        self.refs: set[str] = set()                       # 本段引用了哪些字段（用于多 stats 校验）

    def peek(self, k=0):
        return self.t[self.i + k] if self.i + k < len(self.t) else ("EOF", "", len(self.text), len(self.text))

    def take(self, kind=None, value=None):
        tok = self.peek()
        if (kind and tok[0] != kind) or (value is not None and tok[1] != value):
            raise SyntaxError(f"期望 {value or kind}，实际是 {tok[1] or '结尾'}")
        self.i += 1
        return tok

    def at(self, kind, value=None):
        tok = self.peek()
        return tok[0] == kind and (value is None or tok[1] == value)

    # 优先级：or < and < not < 比较 < 加减 < 乘除 < 一元 < 基本项
    def expr(self):
        f = self.and_()
        while self.at("KW", "or"):
            self.take()
            g, h = f, self.and_()
            f = lambda c, g=g, h=h: bool(g(c)) or bool(h(c))
        return f

    def and_(self):
        f = self.not_()
        while self.at("KW", "and"):
            self.take()
            g, h = f, self.not_()
            f = lambda c, g=g, h=h: bool(g(c)) and bool(h(c))
        return f

    def not_(self):
        if self.at("KW", "not"):
            self.take()
            g = self.not_()
            return lambda c: not g(c)
        return self.cmp()

    def cmp(self):
        f = self.add()
        tok = self.peek()
        if tok[0] == "OP" and tok[1] in ("=", "!=", "<", "<=", ">", ">="):
            self.take()
            g, op = self.add(), _cmp(tok[1])
            return lambda c: op(f(c), g(c))
        if tok[0] == "KW" and tok[1] == "not" and self.peek(1)[1] == "like":
            self.take()
            inner = self._like(f)
            return lambda c: not inner(c)
        if self.at("KW", "like"):
            return self._like(f)
        if self.at("KW", "in"):
            self.take()
            self.take("OP", "[")
            items = [self.add()]
            while self.at("OP", ","):
                self.take()
                items.append(self.add())
            self.take("OP", "]")
            return lambda c: f(c) is not None and f(c) in [g(c) for g in items]
        return f

    def _like(self, f):
        self.take("KW", "like")
        tok = self.take()
        if tok[0] == "REGEX":
            rx = re.compile(tok[1].replace("(?i)", ""), re.I if "(?i)" in tok[1] else 0)
            return lambda c: isinstance(f(c), str) and rx.search(f(c)) is not None
        if tok[0] == "STR":
            return lambda c: isinstance(f(c), str) and tok[1] in f(c)
        raise SyntaxError("like 后面应是 /正则/ 或 \"子串\"")

    def add(self):
        f = self.mul()
        while self.peek()[0] == "OP" and self.peek()[1] in "+-":
            op = _arith(self.take()[1])
            g, h = f, self.mul()
            f = lambda c, g=g, h=h, op=op: op(g(c), h(c))
        return f

    def mul(self):
        f = self.unary()
        while self.peek()[0] == "OP" and self.peek()[1] in "*/%":
            op = _arith(self.take()[1])
            g, h = f, self.unary()
            f = lambda c, g=g, h=h, op=op: op(g(c), h(c))
        return f

    def unary(self):
        if self.at("OP", "-"):
            self.take()
            g = self.unary()
            return lambda c: None if g(c) is None else -g(c)
        return self.primary()

    def primary(self):
        kind, val, *_ = self.peek()
        if kind == "NUM":
            self.take()
            v = float(val) if "." in val else int(val)
            return lambda c: v
        if kind == "STR":
            self.take()
            return lambda c: val
        if self.at("OP", "("):
            self.take()
            f = self.expr()
            self.take("OP", ")")
            return f
        if kind == "ID":
            self.take()
            if self.at("OP", "("):
                return self.call(val.lower())
            if self.agg:
                raise SyntaxError(f"stats 中的字段 {val} 必须放进聚合函数，或写在 by 子句里")
            self.refs.add(val)
            return lambda c: c.get(val)
        raise SyntaxError(f"意外的 {val or '结尾'}")

    def call(self, name):
        self.take("OP", "(")
        if name in AGGREGATES:
            if not self.agg:
                raise SyntaxError(f"聚合函数 {name}() 只能出现在 stats 中")
            if name == "count" and self.at("OP", "*"):
                self.take()
                self.take("OP", ")")
                return lambda rows: _aggregate("count", "*", rows)
            if name == "count" and self.at("OP", ")"):
                self.take()
                return lambda rows: _aggregate("count", "*", rows)
            self.agg = False                              # 聚合函数的参数按“行”求值
            args = [self.expr()]
            while self.at("OP", ","):
                self.take()
                args.append(self.expr())
            self.agg = True
            self.take("OP", ")")
            return lambda rows: _aggregate(name, args, rows)
        if name == "bin":
            period = self.take("PERIOD")[1]
            self.take("OP", ")")
            self.refs.add("@timestamp")
            return _bin(period)
        if name == "if":
            c = self.expr(); self.take("OP", ",")
            a = self.expr(); self.take("OP", ",")
            b = self.expr(); self.take("OP", ")")
            return lambda r: a(r) if c(r) else b(r)
        if name not in ROW_FUNCS:
            raise SyntaxError(f"本地引擎未实现函数 {name}()")
        args = []
        if not self.at("OP", ")"):
            args.append(self.expr())
            while self.at("OP", ","):
                self.take()
                args.append(self.expr())
        self.take("OP", ")")
        fn = ROW_FUNCS[name]
        return lambda c: fn(*[a(c) for a in args])

    def item(self):
        """expr [as alias] → (列名, 闭包)。列名缺省为表达式原文，与控制台一致。"""
        start = self.peek()[2]
        f = self.expr()
        end = self.t[self.i - 1][3]
        name = " ".join(self.text[start:end].split())
        if self.at("KW", "as"):
            self.take()
            name = self.take("ID")[1]
        return name, f

    def items(self, stop=None):
        out = [self.item()]
        while self.at("OP", ","):
            self.take()
            out.append(self.item())
        if stop is None and self.peek()[0] != "EOF":
            raise SyntaxError(f"多余的内容：{self.peek()[1]}")
        return out


# --------------------------------------------------------------------------- 执行管道
def split_stages(text: str):
    toks = tokenize(text)
    stages, cur = [], []
    for tok in toks:
        if tok[0] == "OP" and tok[1] == "|":
            stages.append(cur)
            cur = []
        else:
            cur.append(tok)
    stages.append(cur)
    return [s for s in stages if s]


def run(rows: list[dict], query: str) -> list[dict]:
    stages = split_stages(query)
    cmds = [s[0][1].lower() for s in stages]
    if "stats" in cmds:
        last = max(i for i, c in enumerate(cmds) if c == "stats")
        bad = [c for c in cmds[:last] if c in ("sort", "limit")]
        if bad:
            raise SyntaxError(f"{bad[0]} 必须写在最后一个 stats 之后")
    available = None                                     # 上一个 stats 输出了哪些列
    visible = None                                       # 最后一次 fields/display 指定的输出列
    for toks in stages:
        cmd, body = toks[0][1].lower(), toks[1:]
        p = Parser(body, query)
        if cmd in ("fields", "display"):
            cols = p.items()
            rows = [r | {name: f(r) for name, f in cols} for r in rows]   # 新列并入；原字段仍可被后续命令引用
            visible = [name for name, _ in cols]
        elif cmd == "filter":
            pred = p.expr()
            if p.peek()[0] != "EOF":
                raise SyntaxError(f"filter 多余的内容：{p.peek()[1]}")
            rows = [r for r in rows if pred(r)]
        elif cmd == "stats":
            p.agg = True
            aggs = p.items(stop="by")
            keys = []
            if p.at("KW", "by"):
                p.take()
                p.agg = False
                keys = p.items()
            if available is not None and not p.refs <= available:
                raise SyntaxError(f"后一个 stats 只能引用前一个 stats 的输出列，未定义：{sorted(p.refs - available)}")
            groups: dict[tuple, list] = {}
            for r in rows:
                groups.setdefault(tuple(f(r) for _, f in keys), []).append(r)
            if not keys and not groups:
                groups[()] = []
            rows = []
            for key, grp in groups.items():
                out = {name: v for (name, _), v in zip(keys, key)}
                out.update({name: f(grp) for name, f in aggs})
                rows.append(out)
            available = {n for n, _ in keys} | {n for n, _ in aggs}
            visible = None
        elif cmd == "sort":
            field = p.take("ID")[1]
            desc = p.at("KW", "desc")
            if p.at("KW", "desc") or p.at("KW", "asc"):
                p.take()
            present = [r for r in rows if r.get(field) is not None]
            missing = [r for r in rows if r.get(field) is None]
            rows = sorted(present, key=lambda r: r[field], reverse=desc) + missing
        elif cmd == "limit":
            rows = rows[: int(p.take("NUM")[1])]
        else:
            raise SyntaxError(f"本地引擎不支持命令 {cmd}")
    if visible is not None:
        rows = [{k: r.get(k) for k in visible} for r in rows]
    return rows


# --------------------------------------------------------------------------- 输入输出
def load(path: str | Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            ts = dt.datetime.fromisoformat(r["ts"].replace("Z", "+00:00"))
            r["@timestamp"] = int(ts.timestamp() * 1000)   # 真实服务里它来自 PutLogEvents 的 timestamp
            r["@message"] = line.strip()
            rows.append(r)
    return rows


def _cell(k, v):
    if k == "@timestamp" and isinstance(v, int):
        return _fmt_ts(v)
    if isinstance(v, float):
        return f"{v:.1f}"
    return "" if v is None else str(v)


def show(rows: list[dict], out=sys.stdout) -> None:
    if not rows:
        print("  （无结果）", file=out)
        return
    keys = list(rows[0])
    table = [[_cell(k, r.get(k)) for k in keys] for r in rows]
    width = [max(len(k), *(len(row[j]) for row in table)) for j, k in enumerate(keys)]
    print("  " + "  ".join(k.ljust(w) for k, w in zip(keys, width)), file=out)
    for row in table:
        print("  " + "  ".join(c.ljust(w) for c, w in zip(row, width)), file=out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logfile")
    ap.add_argument("queryfile", nargs="?")
    ap.add_argument("-q", "--query")
    ap.add_argument("--all", metavar="DIR", help="运行目录下全部 .cwli")
    a = ap.parse_args()
    rows = load(a.logfile)
    if a.all:
        for f in sorted(Path(a.all).glob("*.cwli")):
            text = f.read_text(encoding="utf-8")
            title = text.splitlines()[0].lstrip("# ").strip()
            print(f"\n== {f.name}：{title}")
            show(run(rows, text))
        return
    text = a.query if a.query else Path(a.queryfile).read_text(encoding="utf-8")
    show(run(rows, text))


if __name__ == "__main__":
    main()
