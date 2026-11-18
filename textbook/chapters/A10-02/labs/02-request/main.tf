###############################################################################
# 第 18 讲实验 18-2：账户请求的“合入前检查”
#   与 AFT aft-account-request 仓库中的 module 块使用同一组输入；在 git push 之前，
#   用 terraform test 检查公司规则：邮箱域、账户名、OU 写法（含嵌套 OU）、必填标签、
#   变更原因、定制模板名必须存在。全部离线，不需要任何 provider 与凭证。
#
#   注意：在已部署 AFT 的真实仓库里，合入并推送请求就会开户（产生持续费用、跨账户权限）。
###############################################################################
terraform {
  required_version = ">= 1.6.1" # AFT 1.20.0（2026-04）起的最低 Terraform 版本
}

variable "allowed_email_domains" {
  description = "教材示例只允许 .invalid 域名，防止被误用到真实仓库。"
  type        = list(string)
  default     = ["example.invalid"]
}

variable "known_customizations" {
  description = "aft-account-customizations 仓库里实际存在的模板目录名。"
  type        = list(string)
  default     = ["sandbox-customizations", "prod-baseline"]
}

variable "request" {
  type = object({
    control_tower_parameters = object({
      AccountEmail              = string
      AccountName               = string
      ManagedOrganizationalUnit = string
      SSOUserEmail              = string
      SSOUserFirstName          = string
      SSOUserLastName           = string
    })
    account_tags = map(string)
    change_management_parameters = object({
      change_requested_by = string
      change_reason       = string
    })
    custom_fields               = optional(map(string), {})
    account_customizations_name = optional(string, "")
  })

  validation {
    condition = alltrue([for e in [var.request.control_tower_parameters.AccountEmail, var.request.control_tower_parameters.SSOUserEmail] :
    can(regex("^[^@\\s]+@[^@\\s]+$", e)) && contains(var.allowed_email_domains, element(split("@", e), 1))])
    error_message = "邮箱格式不对，或域名不在允许列表中。"
  }

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,49}$", var.request.control_tower_parameters.AccountName))
    error_message = "账户名须为 3–50 位小写字母、数字或连字符，并以字母开头。"
  }

  validation {
    # 顶层 OU 写名字即可；嵌套 OU 用 “名字 (ou-xxxx-xxxxxxxx)”（AFT ≥ 1.6.5）
    condition     = can(regex("^[A-Za-z0-9][A-Za-z0-9 _-]*( \\(ou-[a-z0-9]{4,32}-[a-z0-9]{8,32}\\))?$", var.request.control_tower_parameters.ManagedOrganizationalUnit))
    error_message = "ManagedOrganizationalUnit 应为 OU 名，或嵌套 OU 的 “名字 (ou-id)” 写法。"
  }

  validation {
    condition     = alltrue([for k in ["CostCenter", "Owner"] : contains(keys(var.request.account_tags), k)])
    error_message = "account_tags 必须包含 CostCenter 与 Owner。"
  }

  validation {
    condition     = length(trimspace(var.request.change_management_parameters.change_reason)) >= 10
    error_message = "change_reason 至少 10 个字符，写清为什么开户。"
  }

  validation {
    condition     = var.request.account_customizations_name == "" || contains(var.known_customizations, var.request.account_customizations_name)
    error_message = "account_customizations_name 必须是定制仓库中已存在的模板目录，否则账户定制阶段会失败。"
  }
}

module "account_request" {
  source = "./modules/aft-account-request"

  control_tower_parameters     = var.request.control_tower_parameters
  account_tags                 = var.request.account_tags
  change_management_parameters = var.request.change_management_parameters
  custom_fields                = var.request.custom_fields
  account_customizations_name  = var.request.account_customizations_name
}

output "request" {
  value = module.account_request.request
}
