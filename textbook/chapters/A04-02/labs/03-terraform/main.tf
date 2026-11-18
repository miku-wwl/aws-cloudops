###############################################################################
# 第 09 讲实验 9-3：日志 → 查询 → 事件 → 队列 的最小可验证环境
#   ① 日志组（保留 1 天）+ 指标过滤器（5xx 计数）+ 6 条保存的查询（来自 ../queries/*.cwli）
#   ② 自定义事件总线（Classic）+ 规则（source / detail-type / severity）
#      + SQS 目标（输入转换、重试策略、死信队列）+ 只允许本规则写入的队列策略
#   ③ 可选（enable_alarm_path = true）：指标过滤器 → 告警 → 默认总线 → 同一个值班队列
# 费用：资源本身几乎不收费；写日志、跑查询、发事件、收发消息按量计费；③ 的告警按“告警指标数”计费。
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
    tags = { Course = "cloudops-A04-02", ManagedBy = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "suffix" {
  description = "实验后缀：多轮实验互不覆盖；也是指标命名空间的一部分。"
  type        = string
  default     = "lab01"
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{2,19}$", var.suffix))
    error_message = "suffix 只能包含小写字母、数字和连字符，长度 3–20。"
  }
}

variable "enable_alarm_path" {
  description = "是否加一条“指标过滤器 → 告警 → 默认总线 → 队列”的自动化路径。"
  type        = bool
  default     = false
}

locals {
  prefix    = "a09-${var.suffix}"
  namespace = "CloudOps/A09/${var.suffix}"
  queries   = fileset("${path.module}/../queries", "*.cwli")
  # 允许向队列写入的规则：自定义总线上的异常规则 +（可选）默认总线上的告警规则
  rule_arns = concat([aws_cloudwatch_event_rule.anomaly.arn], aws_cloudwatch_event_rule.alarm_state[*].arn)
}

# ----------------------------------------------------------------------------- ① 日志
resource "aws_cloudwatch_log_group" "app" {
  name              = "/cloudops/a09/${var.suffix}"
  retention_in_days = 1 # 注意：早于保留期的事件会被 PutLogEvents 拒收（tooOldLogEventEndIndex）
}

resource "aws_cloudwatch_log_metric_filter" "http_5xx" {
  name           = "${local.prefix}-http-5xx"
  log_group_name = aws_cloudwatch_log_group.app.name
  pattern        = "{ $.status >= 500 }" # JSON 过滤语法：数值比较，不是字符串匹配

  metric_transformation {
    namespace     = local.namespace
    name          = "Http5xx"
    value         = "1"
    default_value = "0" # 有日志但没有 5xx 的分钟上报 0；完全没有日志的分钟不上报
    unit          = "Count"
  }
}

resource "aws_cloudwatch_query_definition" "saved" {
  for_each        = local.queries
  name            = "a09/${var.suffix}/${trimsuffix(each.value, ".cwli")}"
  log_group_names = [aws_cloudwatch_log_group.app.name]
  query_string    = file("${path.module}/../queries/${each.value}")
}

# ----------------------------------------------------------------------------- ② 事件
resource "aws_cloudwatch_event_bus" "lab" {
  name = local.prefix
}

resource "aws_cloudwatch_event_rule" "anomaly" {
  name           = "${local.prefix}-anomaly"
  description    = "发布系统判定的高等级部署异常 → 值班队列"
  event_bus_name = aws_cloudwatch_event_bus.lab.name
  event_pattern = jsonencode({
    source        = ["cloudops.lab"]
    "detail-type" = ["DeploymentAnomaly"]
    detail = {
      severity = ["high"]
    }
  })
}

resource "aws_sqs_queue" "incidents" {
  name                       = "${local.prefix}-incidents"
  message_retention_seconds  = 3600
  visibility_timeout_seconds = 30
  receive_wait_time_seconds  = 10   # 长轮询：减少空轮询请求
  sqs_managed_sse_enabled    = true # SSE-SQS；不要改成 alias/aws/sqs（EventBridge 无法使用该密钥）
}

resource "aws_sqs_queue" "dlq" {
  name                      = "${local.prefix}-eb-dlq"
  message_retention_seconds = 86400
  sqs_managed_sse_enabled   = true
}

resource "aws_sqs_queue_policy" "incidents" {
  queue_url = aws_sqs_queue.incidents.id
  policy    = local.incidents_policy
}

resource "aws_sqs_queue_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id
  policy    = local.dlq_policy
}

locals {
  incidents_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "OnlyTheseEventBridgeRules"
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.incidents.arn
      Condition = { ArnEquals = { "aws:SourceArn" = local.rule_arns } }
    }]
  })
  dlq_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DeadLettersFromTheseRules"
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.dlq.arn
      Condition = { ArnEquals = { "aws:SourceArn" = local.rule_arns } }
    }]
  })
}

resource "aws_cloudwatch_event_target" "anomaly_to_queue" {
  rule           = aws_cloudwatch_event_rule.anomaly.name
  event_bus_name = aws_cloudwatch_event_bus.lab.name
  target_id      = "incident-queue"
  arn            = aws_sqs_queue.incidents.arn

  input_transformer {
    input_paths = {
      id        = "$.id"
      source    = "$.source"
      type      = "$.detail-type"
      service   = "$.detail.service"
      release   = "$.detail.release"
      severity  = "$.detail.severity"
      errorRate = "$.detail.errorRate"
    }
    # 字符串变量会被自动加引号；数字原样放入。路径在事件里不存在时变量不会生成，所以发布方必须带齐字段。
    input_template = <<-EOT
      {"eventId": <id>, "source": <source>, "type": <type>, "service": <service>,
       "release": <release>, "severity": <severity>, "errorRate": <errorRate>,
       "rule": <aws.events.rule-name>}
    EOT
  }

  retry_policy {
    maximum_event_age_in_seconds = 3600 # 默认 24 小时 / 185 次；值班通知过时就没有意义
    maximum_retry_attempts       = 10
  }

  dead_letter_config {
    arn = aws_sqs_queue.dlq.arn
  }
}

# ----------------------------------------------------------------------------- ③ 可选：告警路径
resource "aws_cloudwatch_metric_alarm" "http_5xx" {
  count               = var.enable_alarm_path ? 1 : 0
  alarm_name          = "${local.prefix}-http-5xx"
  alarm_description   = "最近 3 分钟中至少 2 分钟出现 5xx（数据来自指标过滤器）"
  namespace           = local.namespace
  metric_name         = "Http5xx"
  statistic           = "Sum"
  period              = 60
  evaluation_periods  = 3
  datapoints_to_alarm = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_event_rule" "alarm_state" {
  count       = var.enable_alarm_path ? 1 : 0
  name        = "${local.prefix}-alarm-to-queue"
  description = "告警进入 ALARM 时，把状态变化事件送进同一个值班队列"
  # 不写 event_bus_name = 默认总线；CloudWatch 告警状态变化事件只发往默认总线
  event_pattern = jsonencode({
    source        = ["aws.cloudwatch"]
    "detail-type" = ["CloudWatch Alarm State Change"]
    detail = {
      alarmName = [aws_cloudwatch_metric_alarm.http_5xx[0].alarm_name]
      state     = { value = ["ALARM"] }
    }
  })
}

resource "aws_cloudwatch_event_target" "alarm_to_queue" {
  count     = var.enable_alarm_path ? 1 : 0
  rule      = aws_cloudwatch_event_rule.alarm_state[0].name
  target_id = "incident-queue"
  arn       = aws_sqs_queue.incidents.arn

  retry_policy {
    maximum_event_age_in_seconds = 3600
    maximum_retry_attempts       = 10
  }

  dead_letter_config {
    arn = aws_sqs_queue.dlq.arn
  }
}

# ----------------------------------------------------------------------------- 输出
output "log_group_name" {
  value = aws_cloudwatch_log_group.app.name
}

output "event_bus_name" {
  value = aws_cloudwatch_event_bus.lab.name
}

output "anomaly_rule_name" {
  value = aws_cloudwatch_event_rule.anomaly.name
}

output "anomaly_rule_arn" {
  value = aws_cloudwatch_event_rule.anomaly.arn
}

output "queue_url" {
  value = aws_sqs_queue.incidents.url
}

output "dlq_url" {
  value = aws_sqs_queue.dlq.url
}

output "metric" {
  value = "${local.namespace} / Http5xx"
}

output "saved_queries" {
  value = sort([for q in aws_cloudwatch_query_definition.saved : q.name])
}
