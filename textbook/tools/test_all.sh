#!/usr/bin/env bash
# 运行全部离线测试：Python unittest + Terraform fmt / validate / test（mock provider，不连 AWS、不建资源）。
#
#   bash tools/test_all.sh                              # init 会从 Terraform Registry 安装 provider
#   PLUGIN_DIR=/path/to/provider-mirror bash tools/test_all.sh   # 只从本地目录安装 provider，不联网
#
# 结束后可删除各实验下的 .terraform/（provider 二进制，每个数百 MB；已在 .gitignore 中忽略）。
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
PY=python3; "$PY" -c "import sys" >/dev/null 2>&1 || PY=python

py_total=0; py_fail=0
for d in $(find chapters -name 'test_*.py' -not -path '*/.terraform/*' -exec dirname {} \; | sort -u); do
  out=$(cd "$d" && "$PY" -m unittest 2>&1 | tail -3)
  n=$(echo "$out" | grep -oE 'Ran [0-9]+' | grep -oE '[0-9]+'); n=${n:-0}
  py_total=$((py_total + n))
  if echo "$out" | grep -q '^OK'; then echo "PASS  py  $d  ($n)"; else echo "FAIL  py  $d"; py_fail=$((py_fail + 1)); fi
done

tf_runs=0; tf_fail=0; tf_dirs=0
init_args=(-backend=false -input=false -no-color)
[ -n "${PLUGIN_DIR:-}" ] && init_args+=("-plugin-dir=$PLUGIN_DIR")
for d in $(find chapters -path '*/tests/*.tftest.hcl' -exec dirname {} \; | xargs -n1 dirname | sort -u); do
  tf_dirs=$((tf_dirs + 1)); res=FAIL
  if (cd "$d" && terraform fmt -check -recursive >/dev/null && terraform init "${init_args[@]}" >/dev/null && terraform validate -no-color >/dev/null); then
    out=$(cd "$d" && terraform test -no-color 2>&1 | tail -1)
    echo "$out" | grep -q '^Success!' && res=PASS
  else
    out="fmt / init / validate 未通过"
  fi
  n=$(echo "$out" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+'); tf_runs=$((tf_runs + ${n:-0}))
  [ "$res" = PASS ] || tf_fail=$((tf_fail + 1))
  echo "$res  tf  $d  ($out)"
done

echo "Python：$py_total 个测试，失败目录 $py_fail 个；Terraform：$tf_dirs 个实验、$tf_runs 个 run，失败目录 $tf_fail 个"
[ "$py_fail" -eq 0 ] && [ "$tf_fail" -eq 0 ]
