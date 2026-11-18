# 第 15 讲实验 15-1：一个“订单服务”子模块。terraform_data 只存在于状态中，不创建任何云资源。
variable "service_name" {
  type = string
}

variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment 只能是 dev 或 prod。"
  }
}

variable "release" {
  type = string
}

resource "terraform_data" "release" {
  input = {
    service     = var.service_name
    environment = var.environment
    release     = var.release
  }
  triggers_replace = var.release # 版本一变就“替换”——用来模拟会重建真实资源的属性变化
}

output "id" {
  value = terraform_data.release.id
}
