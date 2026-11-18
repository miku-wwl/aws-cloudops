###############################################################################
# 第 13 讲实验 13-3：AWS Backup 保护一张 DynamoDB 表，并能独立恢复到新表
#   受保护资源：按需计费的 DynamoDB 表（pk/sk），可选 PITR（1–35 天）
#   AWS Backup：专用备份库（实验中允许连同恢复点一起删除）、每日计划、按 ARN 精确选择资源、
#              备份与恢复两个独立的服务角色
# 费用：表与恢复点都只有几 KB；按 Price List，备份存储 0.10 美元/GB·月、恢复 0.15 美元/GB。
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
  region = var.region
  default_tags {
    tags = { Course = "cloudops-A07-01", Chapter = "A07-01", ManagedBy = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "suffix" {
  type    = string
  default = "lab01"
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{2,19}$", var.suffix))
    error_message = "suffix 只能包含小写字母、数字和连字符，长度 3–20。"
  }
}

variable "enable_pitr" {
  description = "是否开启 DynamoDB 时间点恢复（PITR，0.20 美元/GB·月）。"
  type        = bool
  default     = false
}

variable "pitr_days" {
  description = "PITR 可恢复的天数（1–35）。"
  type        = number
  default     = 7
  validation {
    condition     = var.pitr_days >= 1 && var.pitr_days <= 35
    error_message = "PITR 保留期只能是 1–35 天。"
  }
}

locals {
  prefix = "a13-${var.suffix}"
}

# ----------------------------------------------------------------------------- 受保护的表
resource "aws_dynamodb_table" "orders" {
  name         = "${local.prefix}-orders"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  point_in_time_recovery {
    enabled                 = var.enable_pitr
    recovery_period_in_days = var.enable_pitr ? var.pitr_days : null
  }
}

# ----------------------------------------------------------------------------- AWS Backup
resource "aws_backup_vault" "lab" {
  name          = "${local.prefix}-vault"
  force_destroy = true # 仅限实验：destroy 时连同恢复点一起删除。生产应保留，并考虑库锁定
}

data "aws_iam_policy_document" "backup_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["backup.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "backup" {
  name               = "${local.prefix}-backup"
  assume_role_policy = data.aws_iam_policy_document.backup_trust.json
}

resource "aws_iam_role_policy_attachment" "backup" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role" "restore" {
  name               = "${local.prefix}-restore"
  assume_role_policy = data.aws_iam_policy_document.backup_trust.json
}

resource "aws_iam_role_policy_attachment" "restore" {
  role       = aws_iam_role.restore.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

resource "aws_backup_plan" "daily" {
  name = "${local.prefix}-daily"

  rule {
    rule_name                    = "daily-dynamodb"
    target_vault_name            = aws_backup_vault.lab.name
    schedule                     = "cron(0 5 ? * * *)" # 每天 05:00
    schedule_expression_timezone = "UTC"               # 写明时区；不写也默认 UTC
    start_window                 = 60                  # 作业必须在 60 分钟内开始（不是 RTO）
    completion_window            = 180                 # 必须在 180 分钟内完成（不是 RTO）
    recovery_point_tags          = { Chapter = "A07-01" }

    lifecycle {
      delete_after = 7
    }
  }
}

resource "aws_backup_selection" "orders" {
  name         = "${local.prefix}-orders"
  plan_id      = aws_backup_plan.daily.id
  iam_role_arn = aws_iam_role.backup.arn
  resources    = [aws_dynamodb_table.orders.arn] # 按 ARN 精确选择，不按标签扫描
}

# ----------------------------------------------------------------------------- 输出
output "table_name" {
  value = aws_dynamodb_table.orders.name
}

output "table_arn" {
  value = aws_dynamodb_table.orders.arn
}

output "vault_name" {
  value = aws_backup_vault.lab.name
}

output "backup_role_arn" {
  value = aws_iam_role.backup.arn
}

output "restore_role_arn" {
  value = aws_iam_role.restore.arn
}
