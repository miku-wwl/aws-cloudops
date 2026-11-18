###############################################################################
# 第 02 讲实验 2-4（进阶）：用 AWS FIS 向 Lambda 注入 50% 调用错误，持续 2 分钟，
# 并以 SLO 复合告警作为“停止条件”——实验一旦伤到 SLO 就自动终止。
# 前提：02-lambda-reliability 以 enable_fis_extension = true 部署，fis_config_bucket 指向本模块的桶。
# 费用：FIS 按“动作分钟”计费，本实验约 2 个动作分钟；S3 与 Lambda 费用可忽略。
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
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "function_arn" {
  description = "目标函数 ARN（02 模块输出 function_arn）。"
  type        = string
}

variable "stop_alarm_arn" {
  description = "停止条件告警 ARN（02 模块输出 page_alarm_arn）。"
  type        = string
}

variable "config_bucket" {
  description = "FIS 写入故障配置的 S3 桶名（全局唯一）。"
  type        = string
}

resource "aws_s3_bucket" "fis" {
  bucket        = var.config_bucket
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "fis" {
  bucket                  = aws_s3_bucket.fis.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_iam_policy_document" "fis_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["fis.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "fis" {
  name               = "fis-ticket-query-experiment"
  assume_role_policy = data.aws_iam_policy_document.fis_assume.json
}

data "aws_iam_policy_document" "fis" {
  statement {
    sid       = "WriteFaultConfig"
    actions   = ["s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.fis.arn}/FisConfigs/*"]
  }
  statement {
    sid       = "InspectTargets"
    actions   = ["lambda:GetFunction", "tag:GetResources"]
    resources = ["*"]
  }
  statement {
    sid       = "ReadStopCondition"
    actions   = ["cloudwatch:DescribeAlarms"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "fis" {
  name   = "lambda-fault-injection"
  role   = aws_iam_role.fis.id
  policy = data.aws_iam_policy_document.fis.json
}

resource "aws_fis_experiment_template" "lambda_errors" {
  description = "Inject 50% invocation errors into ticket-query for 2 minutes"
  role_arn    = aws_iam_role.fis.arn

  stop_condition {
    source = "aws:cloudwatch:alarm"
    value  = var.stop_alarm_arn
  }

  action {
    name      = "inject-invocation-errors"
    action_id = "aws:lambda:invocation-error"

    parameter {
      key   = "duration"
      value = "PT2M"
    }
    parameter {
      key   = "invocationPercentage"
      value = "50"
    }
    parameter {
      key   = "preventExecution"
      value = "true"
    }

    target {
      key   = "Functions"
      value = "ticket-query"
    }
  }

  target {
    name           = "ticket-query"
    resource_type  = "aws:lambda:function"
    resource_arns  = [var.function_arn]
    selection_mode = "ALL"
  }

  tags = {
    Name = "ticket-query-invocation-errors"
  }
}

output "experiment_template_id" {
  value = aws_fis_experiment_template.lambda_errors.id
}
