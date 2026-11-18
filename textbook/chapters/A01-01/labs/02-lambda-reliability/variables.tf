variable "region" {
  description = "部署区域。"
  type        = string
  default     = "us-east-1"
}

variable "name" {
  description = "函数名，也用作日志组与告警名前缀。"
  type        = string
  default     = "ticket-query"
}

variable "fail_rate" {
  description = "故障注入：0~1 之间的失败比例。0 为正常，0.2 约 20% 调用抛异常。"
  type        = number
  default     = 0

  validation {
    condition     = var.fail_rate >= 0 && var.fail_rate <= 1
    error_message = "fail_rate 必须在 0 到 1 之间。"
  }
}

variable "reserved_concurrency" {
  description = "预留并发。-1 表示不预留；0 表示拒绝全部调用（用来演示 Throttles）。"
  type        = number
  default     = -1
}

variable "slo_target" {
  description = "请求成功率目标（0~1）。"
  type        = number
  default     = 0.999

  validation {
    condition     = var.slo_target > 0.9 && var.slo_target < 1
    error_message = "slo_target 应在 0.9 与 1 之间（例如 0.999）。"
  }
}

variable "slo_interval_hours" {
  description = "SLO 区间长度（小时），默认 30 天。"
  type        = number
  default     = 720
}

variable "enable_fis_extension" {
  description = "为 AWS FIS 的 Lambda 故障动作挂载扩展层并设置所需环境变量（实验 2-4）。"
  type        = bool
  default     = false
}

variable "fis_config_bucket" {
  description = "enable_fis_extension = true 时必填：FIS 写入故障配置的 S3 桶名。"
  type        = string
  default     = null

  # Terraform 1.9 起，变量校验可以引用其他变量
  validation {
    condition     = !var.enable_fis_extension || var.fis_config_bucket != null
    error_message = "启用 FIS 扩展（enable_fis_extension = true）时必须提供 fis_config_bucket。"
  }
}
