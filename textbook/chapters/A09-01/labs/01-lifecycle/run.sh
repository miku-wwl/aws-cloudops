#!/usr/bin/env bash
# 第 15 讲实验 15-1：在本机真实运行 Terraform 生命周期的六个阶段（只用 terraform_data，零云资源、零费用）。
# 用法：./run.sh            输出同时写入 run-output.txt
set -euo pipefail
cd "$(dirname "$0")"
PY=python3; "$PY" -c "import sys" >/dev/null 2>&1 || PY=python
rm -rf work && mkdir work
exec > >(tee run-output.txt) 2>&1
use() { cp "stages/$1" work/main.tf; }
step() { echo; echo "================ $*"; }
plan() {  # $1=计划文件名  其余=额外参数
  local pf="$1"; shift
  (cd work && terraform plan -input=false -no-color -out="$pf" "$@" | grep -E '^  # |^Plan:|^No changes|will no longer be managed|has moved to' || true)
  (cd work && terraform show -json "$pf" > "$pf.json")
}

terraform version | head -1

step "阶段 0：根模块里创建 terraform_data.orders（release=v1）"
use 00_root.tf
(cd work && terraform init -input=false -no-color >/dev/null)
plan 00.tfplan
"$PY" inspect_plan.py work/00.tfplan.json --allow create
(cd work && terraform apply -input=false -no-color 00.tfplan | tail -1)
ID0=$(cd work && terraform state show -no-color terraform_data.orders | grep -E '^\s+id ' | awk -F'"' '{print $2}')
echo "对象 ID：$ID0"

step "阶段 1：收进模块 + moved（期望：no-op，仅地址变化）"
use 01_module.tf
(cd work && terraform init -input=false -no-color >/dev/null)
plan 01.tfplan
"$PY" inspect_plan.py work/01.tfplan.json --allow no-op
(cd work && terraform apply -input=false -no-color 01.tfplan | tail -1)
ID1=$(cd work && terraform state show -no-color module.orders.terraform_data.release | grep -E '^\s+id ' | awk -F'"' '{print $2}')
echo "对象 ID：$ID1  $( [ "$ID0" = "$ID1" ] && echo '（与阶段 0 相同：没有重建）' || echo '（变了！）')"

step "阶段 2：release v1 → v2（期望：replace——由 triggers_replace 引起）"
plan 02.tfplan -var release=v2
"$PY" inspect_plan.py work/02.tfplan.json --allow no-op,create,update || echo "  → 闸门拒绝：替换需要单独审批（本实验在审查后继续）"
(cd work && terraform apply -input=false -no-color 02.tfplan | tail -1)

step "阶段 2b：同样的 v2 再 plan 一次（期望：No changes）"
plan 02b.tfplan -var release=v2

step "阶段 3：模块改名却忘了 moved（只 plan 不 apply；期望：一删一建）"
cp work/main.tf work/main.keep
use 03_rename_without_moved.tf
(cd work && terraform init -input=false -no-color >/dev/null)
plan 03.tfplan
"$PY" inspect_plan.py work/03.tfplan.json --allow create,update,no-op || echo "  → 闸门拒绝：这不是“改个名字”，是销毁并重建"
cp work/main.keep work/main.tf

step "阶段 4：removed + destroy=false（期望：forget，对象不被销毁）"
use 04_removed.tf
(cd work && terraform init -input=false -no-color >/dev/null)
plan 04.tfplan
"$PY" inspect_plan.py work/04.tfplan.json --allow forget
(cd work && terraform apply -input=false -no-color 04.tfplan | tail -1)
echo "状态中剩余的资源：$(cd work && terraform state list | wc -l)"

step "阶段 5：sensitive 变量会不会出现在计划文件里？"
rm -rf work/terraform.tfstate* && use 05_sensitive.tf
plan 05.tfplan
"$PY" inspect_plan.py work/05.tfplan.json --find "Example-Not-A-Real-Secret-42"
(cd work && terraform show -no-color 05.tfplan | grep -E 'password' || true)
