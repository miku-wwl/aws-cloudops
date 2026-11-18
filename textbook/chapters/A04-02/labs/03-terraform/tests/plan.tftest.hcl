# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {
  override_during = plan

  mock_resource "aws_cloudwatch_event_rule" {
    defaults = {
      arn = "arn:aws:events:us-east-1:111122223333:rule/a09-lab01/a09-lab01-anomaly"
    }
  }

  mock_resource "aws_sqs_queue" {
    defaults = {
      arn = "arn:aws:sqs:us-east-1:111122223333:a09-lab01-incidents"
      url = "https://sqs.us-east-1.amazonaws.com/111122223333/a09-lab01-incidents"
    }
  }
}

run "logs_are_short_lived_and_metered" {
  command = plan

  assert {
    condition     = aws_cloudwatch_log_group.app.retention_in_days == 1
    error_message = "实验日志只保留 1 天。"
  }

  assert {
    condition = (
      aws_cloudwatch_log_metric_filter.http_5xx.pattern == "{ $.status >= 500 }" &&
      one(aws_cloudwatch_log_metric_filter.http_5xx.metric_transformation).default_value == "0" &&
      one(aws_cloudwatch_log_metric_filter.http_5xx.metric_transformation).namespace == "CloudOps/A09/lab01"
    )
    error_message = "指标过滤器：JSON 数值比较、默认值 0、命名空间带 suffix。"
  }
}

run "saved_queries_come_from_the_shared_files" {
  command = plan

  assert {
    condition     = length(aws_cloudwatch_query_definition.saved) == 6
    error_message = "../queries 下的 6 个 .cwli 都应成为保存的查询。"
  }

  assert {
    condition     = strcontains(aws_cloudwatch_query_definition.saved["03-error-rate.cwli"].query_string, "sum(if(status >= 500, 1, 0))")
    error_message = "错误率查询必须在同一分组内计算分子和分母。"
  }
}

run "rule_matches_exactly_three_fields" {
  command = plan

  assert {
    condition = (
      aws_cloudwatch_event_rule.anomaly.event_bus_name == "a09-lab01" &&
      jsondecode(aws_cloudwatch_event_rule.anomaly.event_pattern).source == ["cloudops.lab"] &&
      jsondecode(aws_cloudwatch_event_rule.anomaly.event_pattern)["detail-type"] == ["DeploymentAnomaly"] &&
      jsondecode(aws_cloudwatch_event_rule.anomaly.event_pattern).detail.severity == ["high"]
    )
    error_message = "规则必须挂在自定义总线上，并精确匹配 source / detail-type / severity。"
  }
}

run "queue_accepts_only_this_rule" {
  command = plan

  assert {
    condition = (
      jsondecode(aws_sqs_queue_policy.incidents.policy).Statement[0].Principal.Service == "events.amazonaws.com" &&
      jsondecode(aws_sqs_queue_policy.incidents.policy).Statement[0].Condition.ArnEquals["aws:SourceArn"] == [aws_cloudwatch_event_rule.anomaly.arn]
    )
    error_message = "队列策略只允许 EventBridge 代表本规则写入（aws:SourceArn）。"
  }

  assert {
    condition     = jsondecode(aws_sqs_queue_policy.dlq.policy).Statement[0].Condition.ArnEquals["aws:SourceArn"] == [aws_cloudwatch_event_rule.anomaly.arn]
    error_message = "死信队列同样需要授权，否则失败事件连 DLQ 都进不去。"
  }
}

run "target_has_transformer_retry_and_dlq" {
  command = plan

  assert {
    condition = (
      one(aws_cloudwatch_event_target.anomaly_to_queue.retry_policy).maximum_event_age_in_seconds == 3600 &&
      one(aws_cloudwatch_event_target.anomaly_to_queue.retry_policy).maximum_retry_attempts == 10 &&
      one(aws_cloudwatch_event_target.anomaly_to_queue.dead_letter_config).arn == aws_sqs_queue.dlq.arn
    )
    error_message = "目标必须显式设置重试上限与死信队列。"
  }

  assert {
    condition     = strcontains(one(aws_cloudwatch_event_target.anomaly_to_queue.input_transformer).input_template, "<aws.events.rule-name>")
    error_message = "输入模板应带上规则名，便于消费者追溯。"
  }

  assert {
    condition     = aws_sqs_queue.incidents.sqs_managed_sse_enabled == true && aws_sqs_queue.incidents.kms_master_key_id == null
    error_message = "使用 SSE-SQS；不要用 AWS 托管密钥 alias/aws/sqs。"
  }
}

run "alarm_path_is_opt_in" {
  command = plan

  assert {
    condition     = length(aws_cloudwatch_metric_alarm.http_5xx) == 0 && length(aws_cloudwatch_event_rule.alarm_state) == 0
    error_message = "默认不创建告警路径。"
  }
}

run "alarm_path_shares_the_queue" {
  command = plan
  variables {
    enable_alarm_path = true
  }

  assert {
    condition = (
      jsondecode(aws_cloudwatch_event_rule.alarm_state[0].event_pattern).source == ["aws.cloudwatch"] &&
      jsondecode(aws_cloudwatch_event_rule.alarm_state[0].event_pattern).detail.state.value == ["ALARM"] &&
      jsondecode(aws_cloudwatch_event_rule.alarm_state[0].event_pattern).detail.alarmName == ["a09-lab01-http-5xx"]
    )
    error_message = "告警规则：默认总线上的 CloudWatch Alarm State Change，只要 ALARM。"
  }

  assert {
    condition     = length(jsondecode(aws_sqs_queue_policy.incidents.policy).Statement[0].Condition.ArnEquals["aws:SourceArn"]) == 2
    error_message = "开启告警路径后，队列策略要同时允许两条规则。"
  }
}

run "suffix_is_validated" {
  command = plan
  variables {
    suffix = "Lab_01"
  }
  expect_failures = [var.suffix]
}
