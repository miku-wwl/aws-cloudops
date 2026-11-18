# 阶段 3（只做 plan，不 apply）：模块改名，却忘了写 moved
variable "release" {
  type    = string
  default = "v2"
}

module "order_svc" {
  source       = "../modules/order_service"
  service_name = "orders"
  environment  = "dev"
  release      = var.release
}
