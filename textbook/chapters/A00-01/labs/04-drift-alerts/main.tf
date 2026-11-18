###############################################################################
# A00-01 实验 5：LZ 4.0 起，漂移通知改为发送到管理账户的 EventBridge。
# 本模块在管理账户的 Home Region 创建：EventBridge 规则 → SNS 主题 →（可选）邮件订阅。
# 费用：规则与少量 SNS 消息几乎为零；邮件订阅需要收件人点击确认。
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
  region = var.home_region
}

variable "home_region" {
  type    = string
  default = "us-east-1"
}

variable "alert_email" {
  description = "（可选）接收漂移告警的邮箱。"
  type        = string
  default     = null
}

# 注意：不要用 AWS 托管密钥 alias/aws/sns 加密该主题——它的密钥策略不允许
# events.amazonaws.com 使用，EventBridge 将无法投递。需要加密时请使用客户托管密钥，
# 并在密钥策略中授权 events.amazonaws.com 执行 kms:GenerateDataKey* 与 kms:Decrypt。
resource "aws_sns_topic" "drift" {
  name = "controltower-drift-alerts"
}

resource "aws_cloudwatch_event_rule" "drift" {
  name        = "controltower-drift-detected"
  description = "Control Tower LZ 4.0+ drift notifications"
  event_pattern = jsonencode({
    source        = ["aws.controltower"]
    "detail-type" = ["Drift Detected"]
  })
}

resource "aws_cloudwatch_event_target" "sns" {
  rule = aws_cloudwatch_event_rule.drift.name
  arn  = aws_sns_topic.drift.arn

  input_transformer {
    input_paths = {
      type   = "$.detail.driftType"
      msg    = "$.detail.message"
      action = "$.detail.remediationStep"
    }
    input_template = "\"[Control Tower 漂移] <type>：<msg> 处置建议：<action>\""
  }
}

data "aws_iam_policy_document" "topic" {
  statement {
    sid       = "AllowEventBridgePublish"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.drift.arn]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_cloudwatch_event_rule.drift.arn]
    }
  }
}

resource "aws_sns_topic_policy" "drift" {
  arn    = aws_sns_topic.drift.arn
  policy = data.aws_iam_policy_document.topic.json
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alert_email == null ? 0 : 1
  topic_arn = aws_sns_topic.drift.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

output "rule_arn" {
  value = aws_cloudwatch_event_rule.drift.arn
}
