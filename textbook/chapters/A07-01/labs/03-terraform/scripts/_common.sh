# 供其他脚本 source
export AWS_PAGER="" PYTHONIOENCODING=utf-8
REGION="${REGION:-us-east-1}"
PY=python3; "$PY" -c "import sys" >/dev/null 2>&1 || PY=python
CANON="../01-recovery-math/canon.py"
mkdir -p state
TABLE="$(terraform output -raw table_name)"
