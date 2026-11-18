# 阶段 0：资源直接写在根模块里
variable "release" {
  type    = string
  default = "v1"
}

resource "terraform_data" "orders" {
  input = {
    service     = "orders"
    environment = "dev"
    release     = var.release
  }
  triggers_replace = var.release
}
