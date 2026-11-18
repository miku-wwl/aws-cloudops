# terraform init -backend=false && terraform test   —— mock provider，不连 AWS、零费用
mock_provider "aws" {
  mock_data "aws_iam_policy_document" {
    defaults = {
      json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}"
    }
  }
}

run "baseline_is_least_cost_and_observable" {
  command = plan

  assert {
    condition     = aws_lambda_function.fn.runtime == "python3.14" && aws_lambda_function.fn.architectures[0] == "arm64"
    error_message = "应使用受支持的 Python 3.14 运行时与 arm64 架构。"
  }
  assert {
    condition     = aws_cloudwatch_log_group.fn.retention_in_days == 1
    error_message = "实验日志组应只保留 1 天。"
  }
  assert {
    condition     = aws_lambda_function.fn.environment[0].variables["FAIL_RATE"] == "0"
    error_message = "基线状态不应注入故障。"
  }
}

run "burn_rate_thresholds_match_formula" {
  command = plan

  assert {
    condition     = abs(aws_cloudwatch_metric_alarm.burn["fast-long"].threshold - 0.0144) < 1e-9
    error_message = "1 小时窗口：14.4 × 0.1% = 1.44%。"
  }
  assert {
    condition     = abs(aws_cloudwatch_metric_alarm.burn["slow-long"].threshold - 0.006) < 1e-9
    error_message = "6 小时窗口：6 × 0.1% = 0.6%。"
  }
  assert {
    condition     = aws_cloudwatch_metric_alarm.burn["fast-short"].threshold == aws_cloudwatch_metric_alarm.burn["fast-long"].threshold
    error_message = "长短窗口使用同一个阈值，只是时间范围不同。"
  }
  assert {
    condition     = strcontains(aws_cloudwatch_composite_alarm.page.alarm_rule, "ticket-query-burn-fast-short")
    error_message = "复合告警必须同时引用短窗口告警。"
  }
}

run "fault_injection_is_a_variable_change" {
  command = plan
  variables {
    fail_rate = 0.2
  }

  assert {
    condition     = aws_lambda_function.fn.environment[0].variables["FAIL_RATE"] == "0.2"
    error_message = "故障注入只改变 FAIL_RATE 一个参数。"
  }
}

run "reject_invalid_fail_rate" {
  command = plan
  variables {
    fail_rate = 1.5
  }
  expect_failures = [var.fail_rate]
}

run "fis_extension_wires_layer_and_env" {
  command = plan
  variables {
    enable_fis_extension = true
    fis_config_bucket    = "my-fis-config-bucket"
  }
  override_data {
    target = data.aws_ssm_parameter.fis_layer[0]
    values = {
      insecure_value = "arn:aws:lambda:us-east-1:211125607513:layer:aws-fis-extension-arm64:436"
    }
  }

  assert {
    condition     = aws_lambda_function.fn.environment[0].variables["AWS_LAMBDA_EXEC_WRAPPER"] == "/opt/aws-fis/bootstrap"
    error_message = "FIS 扩展需要 AWS_LAMBDA_EXEC_WRAPPER=/opt/aws-fis/bootstrap。"
  }
  assert {
    condition     = length(aws_lambda_function.fn.layers) == 1
    error_message = "应挂载 FIS 扩展层。"
  }
}

run "fis_extension_requires_bucket" {
  command = plan
  variables {
    enable_fis_extension = true
  }
  override_data {
    target = data.aws_ssm_parameter.fis_layer[0]
    values = {
      insecure_value = "arn:aws:lambda:us-east-1:211125607513:layer:aws-fis-extension-arm64:436"
    }
  }
  expect_failures = [var.fis_config_bucket]
}
