# AWS CloudOps 工程教材 · 2026 修订版（源稿与工具链）

19 讲教材的可编辑源稿、图表源码、控制台截图与实验工程。每讲一个目录，
构建产物为 `dist/pdf/<讲次>.pdf`。

## 目录结构

```
textbook/
  tools/                 构建工具（所有讲共用）
    build.py             chapter.md → HTML → PDF → QA（联系表 + 自动检查）
    style.css            版式系统（参照《高中物理·加速度》样章）
    figlib.py            SVG 机制图 / 架构图绘图库
    shot.py              控制台截图裁剪与规范化
    pages.py             两页一图的逐页审阅渲染
    package.py           打包两个最终 ZIP，并校验 ZIP 与 PDF、源稿逐字节一致
    test_all.sh          运行全部离线测试（Python unittest + terraform fmt/validate/test）
    console_prep.js      控制台截图前的页面内脱敏脚本（模板；真实值放在 *.local.js）
    capture_window.ps1   （备用）原生分辨率窗口截图
    edge_window.ps1      （备用）在不抢焦点的前提下恢复浏览器窗口
  chapters/<id>/
    chapter.md           正文源稿（Pandoc Markdown + fenced divs）
    figures/figs.py      本讲全部图的源码 → *.svg
    screenshots/*.jpg    控制台实拍（已脱敏）
    labs/                实验工程（Terraform / 脚本 / 测试）
  dist/pdf/              生成的 PDF
  dist/*.zip             两个最终 ZIP（PDF 合集；源稿与实验工程）
```

## 构建

依赖：Python 3.11+（PyYAML、Pygments、Pillow、pypdf）、Pandoc ≥ 3.8、Google Chrome（headless 打印）、
poppler（pdftoppm，用于 QA）。字体：Noto Sans SC / Noto Serif SC、Cascadia Mono。

```bash
python tools/build.py A00-01            # 生成图 + HTML + PDF + QA
python tools/build.py A00-01 --no-figs  # 跳过重新生成图
python tools/pages.py dist/pdf/<file>.pdf chapters/A00-01/build/pages 66   # 逐页审阅图
python tools/package.py                 # 重新打包两个 ZIP 并校验一致性
python tools/package.py --verify        # 只校验
bash tools/test_all.sh                  # 全部离线测试（--python / --terraform 只跑一部分）
```

`chapters/*/build/` 是构建中间产物，`labs/**/.terraform/` 是 provider 缓存，都不入库（见仓库根目录 `.gitignore`）。

## 源稿约定（Pandoc Markdown）

| 元素 | 写法 |
|---|---|
| 章首页 | `::::: cover` … `:::::`，内含 kicker、`#` 标题、subtitle、`cover-meta`、`scenario`、学习目标 |
| 小节开篇（问题式大标题） | `::: opener` + `[一 · 机制]{.kicker}` + `# 问题？` + `[副标题]{.subtitle}` |
| 编号小节 | `## 标题`（CSS 自动编号 01、02…；`{.nonum}` 不编号） |
| 提示框 | `::: scenario / tip / note / why / key / think / warn / cost / safety / answer` |
| 公式 / 模型 | `::: formula` |
| 卡片 | `:::: cards`（`{.cards .three}` 三列）内含 `::: {.card title="…"}` |
| 易混判断 | `::: pitfalls` + 有序列表 |
| 例题 | `:::: {.example title="例题 1-1｜…"}`，步骤用 `::: steps`，答案 `::: answer` |
| 实验 | `:::: {.lab title="实验 1-1｜…"}`，元信息 `::: labmeta` + `- **键**：值` |
| 故障卡 | `::: {.fault title="故障 1｜…"}` + 定义列表（现象/根因/验证/修复） |
| 练习 / 答案 | `::: {.exercise title="练习 1｜…"}` / `::: {.solution title="1"}` |
| 本讲要点 | `:::: summary` 内含 `::: {.card tag="…"}` |
| 图 | `![图 1-1｜说明](figures/x.svg)`；控制台截图加 `{.shot}` |
| 代码 | ```` ```{.hcl title="main.tf"} ````；终端输出用 `.console` |

## 截图与脱敏

截图在已登录的浏览器中只读采集；采集前在页面内把账户 ID、账户别名替换为 AWS 文档示例值
`111122223333` / `cloudops-lab`，并用根元素 CSS zoom 把版面统一为约 1400 px 宽。
任何会创建资源或产生费用的按钮都不点击（例如 Control Tower 向导第 2 步的 Create Organization）。
`tools/console_prep.js` 中的替换表是占位值：复制为 `tools/console_prep.local.js` 后填入自己的账户号、别名、邮箱与用户名
（`*.local.*` 已被 `.gitignore` 忽略）。`tools/package.py` 打包前会用本机的 `tools/sensitive.local.txt`
（每行一个正则，同样不入库）扫描全部源稿，命中即停止。

## 实验与验证（V1.0，2026-11-18）

- 每讲 `labs/README.md` 列出实验、是否改动 AWS、费用与验证状态；全部 Terraform 实验的离线测试、只读 plan
  与 apply 创建条件汇总在仓库根目录 README 的“实验与验证级别”。
- 全部 Python 实验共 119 个单元测试（22 个目录），`cd chapters/<id>/labs/<lab> && python -m unittest` 可复现
  （第 07 讲 `02-envelope` 需要 `pip install cryptography`）。
- 18 个 Terraform 实验带 `tests/*.tftest.hcl`（全部 mock provider，不连 AWS），共 95 个 run；另有 5 个根模块
  没有 tests，只做 `fmt -check` 与 `validate`。
- 只读 plan **不是零资源**：多数实验的默认 plan 就会列出 apply 时要创建的资源（例如 3-2 默认 12 to add）；
  只有 17-2、19-4 默认 0 个资源，打开 `enable_paid_lab` / `enable` 后才创建，18-2 不含任何 AWS 资源。
- 书中所有“本书实测输出”都来自只读 API、免费的计算型 API（策略模拟器、Access Analyzer、
  TestEventPattern、Price List）、本地运行或只读 `terraform plan`；V1.0 没有对 AWS 执行任何 apply。
- `.github/workflows/ci.yml` 在每次推送时离线运行 `tools/package.py --verify` 与 `tools/test_all.sh`，不使用任何凭证。
