###############################################################################
# 第 08 讲实验 8-2：三条告警 + 一条复合告警，作用于自定义指标 Lab/CloudOps（Service=checkout）
#   errors      ：Sum(Errors) ≥ 1，2/3，缺失 = notBreaching（稀疏指标）
#   heartbeat   ：Min(Heartbeat) < 1，3/3，缺失 = breaching（应持续上报的指标）
#   error_rate  ：指标数学 100×Errors/Requests ≥ 5%，且 Requests ≥ 最小样本（低流量保护）
#   page        ：复合告警 = error_rate OR heartbeat
# 费用：标准分辨率告警按“告警引用的指标数”计费；自定义指标按指标数计费（均在免费额度外才收费）。
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
    tags = { Course = "cloudops-A04-01", ManagedBy = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "service" {
  description = "维度 Service 的值。告警与上报脚本必须完全一致。"
  type        = string
  default     = "checkout"
}

variable "min_requests" {
  description = "错误率告警的最小样本：每分钟请求数低于它时不按错误率判断。"
  type        = number
  default     = 50
}

variable "alarm_topic_arn" {
  description = "（可选）告警通知 SNS 主题；为 null 时不发送通知。"
  type        = string
  default     = null
}

locals {
  ns      = "Lab/CloudOps"
  dims    = { Service = var.service }
  actions = var.alarm_topic_arn == null ? [] : [var.alarm_topic_arn]
}

resource "aws_cloudwatch_metric_alarm" "errors" {
  alarm_name          = "a08-${var.service}-errors"
  alarm_description   = "任意 2 个 1 分钟窗口（共 3 个）出现 5xx"
  namespace           = local.ns
  metric_name         = "Errors"
  dimensions          = local.dims
  statistic           = "Sum"
  period              = 60
  evaluation_periods  = 3
  datapoints_to_alarm = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.actions
  ok_actions          = local.actions
}

resource "aws_cloudwatch_metric_alarm" "heartbeat" {
  alarm_name          = "a08-${var.service}-heartbeat-missing"
  alarm_description   = "连续 3 分钟没有心跳"
  namespace           = local.ns
  metric_name         = "Heartbeat"
  dimensions          = local.dims
  statistic           = "Minimum"
  period              = 60
  evaluation_periods  = 3
  datapoints_to_alarm = 3
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"
  alarm_actions       = local.actions
}

resource "aws_cloudwatch_metric_alarm" "error_rate" {
  alarm_name          = "a08-${var.service}-error-rate"
  alarm_description   = "错误率 ≥ 5%（仅当每分钟请求数 ≥ ${var.min_requests}）"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = 5
  evaluation_periods  = 3
  datapoints_to_alarm = 2
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "rate"
    label       = "error rate (%) with min-traffic guard"
    expression  = "IF(req >= ${var.min_requests}, 100 * err / req, 0)"
    return_data = true
  }

  dynamic "metric_query" {
    for_each = { req = "Requests", err = "Errors" }
    content {
      id = metric_query.key
      metric {
        namespace   = local.ns
        metric_name = metric_query.value
        dimensions  = local.dims
        period      = 60
        stat        = "Sum"
      }
    }
  }
}

resource "aws_cloudwatch_composite_alarm" "page" {
  alarm_name        = "a08-${var.service}-page"
  alarm_description = "需要人工介入：错误率过高，或服务失联"
  alarm_rule        = "ALARM(\"${aws_cloudwatch_metric_alarm.error_rate.alarm_name}\") OR ALARM(\"${aws_cloudwatch_metric_alarm.heartbeat.alarm_name}\")"
  alarm_actions     = local.actions
}

output "alarm_names" {
  value = [
    aws_cloudwatch_metric_alarm.errors.alarm_name,
    aws_cloudwatch_metric_alarm.heartbeat.alarm_name,
    aws_cloudwatch_metric_alarm.error_rate.alarm_name,
    aws_cloudwatch_composite_alarm.page.alarm_name,
  ]
}
