# 供其他脚本 source：选择 Python，并把临时文件路径转换成 aws.exe 能读的形式（Git Bash 下）。
export AWS_PAGER=""
PY=python3; "$PY" -c "import sys" >/dev/null 2>&1 || PY=python
winpath() { if command -v cygpath >/dev/null 2>&1; then cygpath -w "$1"; else printf '%s' "$1"; fi; }
