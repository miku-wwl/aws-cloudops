# 供其他脚本 source。
export AWS_PAGER=""
REGION="${REGION:-us-east-1}"
ID="$(terraform output -raw instance_id 2>/dev/null || true)"
need_instance() { [ -n "$ID" ] && [ "$ID" != "null" ] || { echo "没有实验实例：先 terraform apply -var create_lab_instance=true"; exit 1; }; }
