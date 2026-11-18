###############################################################################
# 第 19 讲实验 19-4：把“归属、保留期限、预算”写进代码
#   enable = false（默认）：plan 中 0 个资源。
#   enable = true：
#     - 日志组：保留 7 天（保留策略，不是“销毁计时器”）
#     - 成本分摊标签 Project 激活（aws_ce_cost_allocation_tag；标签键必须已经出现在账单数据中）
#     - 预算：按 Project 标签过滤；实际花费超过 80%、预测超过 100% 时发邮件
#       （没有 Budget Action 的预算不收费；带 Action 的预算每账户前两个免费）
# 费用：日志组按写入与存储计费（本实验不写入）；预算 0 元；标签激活 0 元。
###############################################################################
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = local.lab_tags
  }
}

variable "enable" {
  type    = bool
  default = false
}

variable "project" {
  type    = string
  default = "finops-lab"
}

variable "owner" {
  type    = string
  default = "platform-team"
}

variable "expires_on" {
  description = "计划回收日期（YYYY-MM-DD）。它只是给盘点与审批看的标记，不会自动删除任何东西。"
  type        = string
  default     = "2026-11-25"
  validation {
    condition     = can(regex("^\\d{4}-\\d{2}-\\d{2}$", var.expires_on))
    error_message = "expires_on 必须是 YYYY-MM-DD。"
  }
}

variable "monthly_limit_usd" {
  type    = number
  default = 5
}

variable "notify_email" {
  description = "预算通知邮箱；为空则不创建预算。"
  type        = string
  default     = ""
}

locals {
  lab_tags = {
    Project   = var.project
    Owner     = var.owner
    ExpiresOn = var.expires_on
    ManagedBy = "terraform"
  }
}

resource "aws_cloudwatch_log_group" "lab" {
  count             = var.enable ? 1 : 0
  name              = "/finops/${var.project}/demo"
  retention_in_days = 7
}

resource "aws_ce_cost_allocation_tag" "project" {
  count   = var.enable ? 1 : 0
  tag_key = "Project"
  status  = "Active"
}

resource "aws_budgets_budget" "lab" {
  count        = var.enable && var.notify_email != "" ? 1 : 0
  name         = "${var.project}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_limit_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name   = "TagKeyValue"
    values = [format("user:Project$%s", var.project)] # 只有激活后的成本分摊标签才能用来过滤
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.notify_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.notify_email]
  }
}
