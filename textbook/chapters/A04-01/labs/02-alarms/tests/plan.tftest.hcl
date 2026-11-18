# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {}

run "errors_is_sparse_2_of_3" {
  command = plan

  assert {
    condition = (
      aws_cloudwatch_metric_alarm.errors.evaluation_periods == 3 &&
      aws_cloudwatch_metric_alarm.errors.datapoints_to_alarm == 2 &&
      aws_cloudwatch_metric_alarm.errors.treat_missing_data == "notBreaching" &&
      aws_cloudwatch_metric_alarm.errors.statistic == "Sum"
    )
    error_message = "错误数告警：Sum、2/3、缺失视为未越界。"
  }
}

run "heartbeat_treats_silence_as_failure" {
  command = plan

  assert {
    condition = (
      aws_cloudwatch_metric_alarm.heartbeat.treat_missing_data == "breaching" &&
      aws_cloudwatch_metric_alarm.heartbeat.statistic == "Minimum" &&
      aws_cloudwatch_metric_alarm.heartbeat.comparison_operator == "LessThanThreshold"
    )
    error_message = "心跳告警：Minimum < 1，缺失视为越界。"
  }
}

run "same_dimensions_everywhere" {
  command = plan

  assert {
    condition = (
      aws_cloudwatch_metric_alarm.errors.dimensions["Service"] == "checkout" &&
      aws_cloudwatch_metric_alarm.heartbeat.dimensions["Service"] == "checkout"
    )
    error_message = "告警维度必须与上报脚本一致（Service=checkout）。"
  }
}

run "error_rate_has_min_traffic_guard" {
  command = plan
  variables {
    min_requests = 100
  }

  assert {
    condition     = strcontains(one([for q in aws_cloudwatch_metric_alarm.error_rate.metric_query : q.expression if q.id == "rate"]), "req >= 100")
    error_message = "错误率表达式必须带最小样本保护。"
  }
}

run "no_actions_without_topic" {
  command = plan

  assert {
    condition     = length(aws_cloudwatch_metric_alarm.errors.alarm_actions) == 0
    error_message = "未提供 SNS 主题时不应配置告警动作。"
  }
}
