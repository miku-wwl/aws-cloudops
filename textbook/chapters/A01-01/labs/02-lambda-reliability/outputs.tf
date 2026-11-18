output "function_name" {
  value = aws_lambda_function.fn.function_name
}

output "function_arn" {
  value = aws_lambda_function.fn.arn
}

output "region" {
  value = var.region
}

output "burn_rate_thresholds" {
  description = "每条燃烧率告警的窗口（秒）、燃烧率与错误率阈值，便于评审。"
  value = {
    for k, v in local.burn_specs : k => {
      window_seconds        = v.period
      burn_rate             = v.burn
      error_ratio_threshold = v.threshold
    }
  }
}

output "page_alarm_arn" {
  description = "复合告警 ARN：可作为 FIS 实验的停止条件。"
  value       = aws_cloudwatch_composite_alarm.page.arn
}
