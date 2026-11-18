variable "home_region" {
  description = "Control Tower 主区域（Home Region）。落地后不能更改。"
  type        = string
  default     = "us-east-1"
}

variable "governed_regions" {
  description = "受治理区域列表，必须包含 home_region。"
  type        = list(string)
  default     = ["us-east-1"]
}

variable "landing_zone_version" {
  description = "Landing Zone 版本。本教材以 4.0 为准。"
  type        = string
  default     = "4.0"
}

variable "auto_enrollment" {
  description = "true 时设置 remediation_types = [\"INHERITANCE_DRIFT\"]，即控制台中的“自动账户注册”。"
  type        = bool
  default     = true
}

variable "integrations" {
  description = <<-EOT
    LZ 4.0 服务集成开关。依赖链（来自 AWS 文档）：
      security_roles    → 需要 config
      access_management → 需要 security_roles
      backup            → 需要 security_roles
      centralized_logging、config 无前置依赖
  EOT
  type = object({
    config              = bool
    centralized_logging = bool
    security_roles      = bool
    access_management   = bool
    backup              = bool
  })
  default = {
    config              = true
    centralized_logging = true
    security_roles      = true
    access_management   = true
    backup              = false
  }
}

variable "integration_accounts" {
  description = "服务集成账户 ID。必须事先创建，并放在同一个根级 OU（即指定的 Security OU）下。"
  type = object({
    logging        = optional(string)
    security_roles = optional(string)
    config         = optional(string)
    backup_central = optional(string)
    backup_admin   = optional(string)
  })
  default = {}
}

variable "log_retention_days" {
  description = "集中日志桶的对象保留天数。"
  type        = number
  default     = 365
}

variable "access_log_retention_days" {
  description = "访问日志桶的对象保留天数。"
  type        = number
  default     = 3650
}

variable "kms_key_arn" {
  description = "（可选）加密日志桶 / Config 桶 / 备份库的 KMS 客户托管密钥 ARN。"
  type        = string
  default     = null
}
