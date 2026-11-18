# 阶段 1：重构——把资源收进模块，用 moved 告诉 Terraform“这是同一个对象”
variable "release" {
  type    = string
  default = "v1"
}

module "orders" {
  source       = "../modules/order_service"
  service_name = "orders"
  environment  = "dev"
  release      = var.release
}

moved {
  from = terraform_data.orders
  to   = module.orders.terraform_data.release
}
