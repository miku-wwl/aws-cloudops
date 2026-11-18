#!/usr/bin/env bash
# 运行全部离线测试。不连接 AWS、不需要 AWS 凭证、不创建任何云资源：
#   - Python：各实验目录下的 unittest；
#   - Terraform：带 tests/ 的实验做 fmt -check、init、validate、test（tests 全部使用 mock_provider）；
#     没有 tests/ 的根模块（依赖前一实验的输出，或只用于演示）做 fmt -check、init、validate。
#
#   bash tools/test_all.sh                 # 全部
#   bash tools/test_all.sh --python        # 只跑 Python
#   bash tools/test_all.sh --terraform     # 只跑 Terraform
#   PLUGIN_DIR=/path/to/provider-mirror bash tools/test_all.sh   # 只从本地目录安装 provider，不访问 Registry
#
# init 默认从 Terraform Registry 下载 provider（不访问 AWS）。结束后可删除各实验下的 .terraform/ 与
# .terraform.lock.hcl（已在 .gitignore 中忽略）。任何一项失败都会打印该项的输出，并以非零状态退出（CI 用）。
set -uo pipefail
cd "$(dirname "$0")/.."

run_py=1; run_tf=1
case "${1:-}" in
  "") ;;
  --python) run_tf=0 ;;
  --terraform) run_py=0 ;;
  *) echo "用法：bash tools/test_all.sh [--python | --terraform]" >&2; exit 2 ;;
esac

export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
PY=python3; "$PY" -c "import sys" >/dev/null 2>&1 || PY=python

show_fail() { echo "---- $1 的输出（末尾 40 行）----"; echo "$2" | tail -40; echo "----"; }

# ---------------------------------------------------------------- Python
py_dirs=0; py_total=0; py_fail=0
if [ "$run_py" -eq 1 ]; then
  for d in $(find chapters -name 'test_*.py' -not -path '*/.terraform/*' -exec dirname {} \; | sort -u); do
    py_dirs=$((py_dirs + 1))
    out=$(cd "$d" && "$PY" -m unittest 2>&1)
    n=$(echo "$out" | grep -oE '^Ran [0-9]+' | grep -oE '[0-9]+' | tail -1); n=${n:-0}
    py_total=$((py_total + n))
    if echo "$out" | tail -3 | grep -q '^OK'; then
      echo "PASS  py  $d  ($n)"
    else
      py_fail=$((py_fail + 1)); echo "FAIL  py  $d"; show_fail "$d" "$out"
    fi
  done
fi

# ---------------------------------------------------------------- Terraform
tf_dirs=0; tf_runs=0; tfv_dirs=0; tf_fail=0
if [ "$run_tf" -eq 1 ]; then
  init_args=(-backend=false -input=false -no-color)
  [ -n "${PLUGIN_DIR:-}" ] && init_args+=("-plugin-dir=$PLUGIN_DIR")

  # 在目录 $1 中运行 terraform 的一个子命令；失败时把输出留在 $out
  tf_step() { local d=$1; shift; out=$(cd "$d" && terraform "$@" 2>&1) || { out="terraform $1 失败：
$out"; return 1; }; }
  tf_prepare() { tf_step "$1" fmt -check -recursive && tf_step "$1" init "${init_args[@]}" && tf_step "$1" validate -no-color; }

  # 1) 带 tests/ 的实验
  for d in $(find chapters -path '*/tests/*.tftest.hcl' -not -path '*/.terraform/*' -exec dirname {} \; | xargs -n1 dirname | sort -u); do
    tf_dirs=$((tf_dirs + 1))
    if tf_prepare "$d" && tf_step "$d" test -no-color; then
      summary=$(echo "$out" | tail -1)
      n=$(echo "$summary" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+'); tf_runs=$((tf_runs + ${n:-0}))
      echo "PASS  tf  $d  ($summary)"
    else
      tf_fail=$((tf_fail + 1)); echo "FAIL  tf  $d"; show_fail "$d" "$out"
    fi
  done

  # 2) 没有 tests/ 的根模块（stages/ 由第 15 讲自己的脚本运行，modules/ 由调用方覆盖）
  for d in $(find chapters -name '*.tf' -not -path '*/.terraform/*' -not -path '*/tests/*' \
               -not -path '*/modules/*' -not -path '*/stages/*' -exec dirname {} \; | sort -u); do
    [ -d "$d/tests" ] && continue
    tfv_dirs=$((tfv_dirs + 1))
    if tf_prepare "$d"; then
      echo "PASS  tf  $d  (fmt / validate；无 tests)"
    else
      tf_fail=$((tf_fail + 1)); echo "FAIL  tf  $d"; show_fail "$d" "$out"
    fi
  done
fi

# ---------------------------------------------------------------- 汇总
[ "$run_py" -eq 1 ] && echo "Python：$py_dirs 个实验目录、$py_total 个测试，失败 $py_fail 个目录"
[ "$run_tf" -eq 1 ] && echo "Terraform：$tf_dirs 个实验 terraform test 共 $tf_runs 个 run；另 $tfv_dirs 个根模块 fmt / validate；失败 $tf_fail 个"
# 一个也没发现时视为失败（防止目录结构变化后测试被悄悄跳过）
[ "$run_py" -eq 0 ] || [ "$py_dirs" -gt 0 ] || { echo "没有发现 Python 测试" >&2; exit 1; }
[ "$run_tf" -eq 0 ] || [ "$tf_dirs" -gt 0 ] || { echo "没有发现 Terraform 测试" >&2; exit 1; }
[ "$py_fail" -eq 0 ] && [ "$tf_fail" -eq 0 ]
