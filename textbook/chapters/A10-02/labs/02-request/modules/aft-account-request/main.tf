# 第 18 讲实验 18-2：与 AFT 官方 aft-account-request 模块“同形状”的离线替身。
# 真实的 AFT 模块会把请求写进 AFT 管理账户的 DynamoDB 表，从而触发开户与定制；
# 这个替身只声明同样的输入、输出规范化后的请求 JSON，不连接 AWS，可以在任何机器上 terraform test。
terraform {
  required_version = ">= 1.6.1"
}

variable "control_tower_parameters" {
  type = object({
    AccountEmail              = string
    AccountName               = string
    ManagedOrganizationalUnit = string
    SSOUserEmail              = string
    SSOUserFirstName          = string
    SSOUserLastName           = string
  })
}

variable "account_tags" {
  type    = map(string)
  default = {}
}

variable "change_management_parameters" {
  type = object({
    change_requested_by = string
    change_reason       = string
  })
}

variable "custom_fields" {
  type    = map(string)
  default = {}
}

variable "account_customizations_name" {
  type    = string
  default = ""
}

output "request" {
  description = "AFT 会存入请求表的内容（规范化后的 JSON）。"
  value = jsonencode({
    id                           = var.control_tower_parameters.AccountEmail
    control_tower_parameters     = var.control_tower_parameters
    account_tags                 = var.account_tags
    change_management_parameters = var.change_management_parameters
    custom_fields                = var.custom_fields
    account_customizations_name  = var.account_customizations_name
  })
}
