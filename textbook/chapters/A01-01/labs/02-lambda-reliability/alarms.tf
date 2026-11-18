###############################################################################
# 告警：一个“有错就响”的对照告警 + 基于 SLO 的多窗口燃烧率告警
#
# 失败率口径（调用方视角）：(Errors + Throttles) / (Invocations + Throttles)
#   —— Invocations 不包含被限流的请求，所以分子分母都要把 Throttles 加回来。
# 燃烧率阈值 = 允许消耗的预算比例 × 区间长度 / 窗口长度
#   2% 预算 / 1 小时  → 14.4；5% 预算 / 6 小时 → 6（30 天区间）
# 错误率阈值 = 燃烧率阈值 × (1 − SLO)，保留 6 位小数（避免 0.01439999… 这类精度噪声）
###############################################################################

locals {
  budget_ratio = 1 - var.slo_target

  burn_windows = {
    fast = { budget = 0.02, long = 3600, short = 300 }   # 1 小时 / 5 分钟
    slow = { budget = 0.05, long = 21600, short = 1800 } # 6 小时 / 30 分钟
  }

  burn_specs = merge([
    for k, w in local.burn_windows : {
      "${k}-long" = {
        period    = w.long
        burn      = w.budget * var.slo_interval_hours / (w.long / 3600)
        threshold = tonumber(format("%.6f", w.budget * var.slo_interval_hours / (w.long / 3600) * local.budget_ratio))
      }
      "${k}-short" = {
        period    = w.short
        burn      = w.budget * var.slo_interval_hours / (w.long / 3600)
        threshold = tonumber(format("%.6f", w.budget * var.slo_interval_hours / (w.long / 3600) * local.budget_ratio))
      }
    }
  ]...)

  lambda_metrics = { err = "Errors", inv = "Invocations", thr = "Throttles" }
}

# 对照组：只要出现一次函数错误就进入 ALARM（灵敏但噪声大）
resource "aws_cloudwatch_metric_alarm" "errors_any" {
  alarm_name          = "${var.name}-errors-any"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = 60
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  actions_enabled     = false
  dimensions          = { FunctionName = aws_lambda_function.fn.function_name }
}

# 燃烧率告警：每个窗口一条，指标数学计算“调用方失败率”
resource "aws_cloudwatch_metric_alarm" "burn" {
  for_each = local.burn_specs

  alarm_name          = "${var.name}-burn-${each.key}"
  alarm_description   = "SLO ${var.slo_target}：失败率超过燃烧率 ${each.value.burn} 对应的阈值"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = each.value.threshold
  treat_missing_data  = "notBreaching"
  actions_enabled     = false

  metric_query {
    id          = "ratio"
    expression  = "IF((inv + thr) > 0, (err + thr) / (inv + thr), 0)"
    label       = "caller failure ratio"
    return_data = true
  }

  dynamic "metric_query" {
    for_each = local.lambda_metrics
    content {
      id = metric_query.key
      metric {
        namespace   = "AWS/Lambda"
        metric_name = metric_query.value
        period      = each.value.period
        stat        = "Sum"
        dimensions  = { FunctionName = aws_lambda_function.fn.function_name }
      }
    }
  }
}

# 只有“长窗口证明问题严重”且“短窗口证明问题仍在发生”时才呼叫值班
resource "aws_cloudwatch_composite_alarm" "page" {
  alarm_name      = "${var.name}-slo-page"
  actions_enabled = false
  alarm_rule = join(" OR ", [
    for k in keys(local.burn_windows) :
    "(ALARM(\"${aws_cloudwatch_metric_alarm.burn["${k}-long"].alarm_name}\") AND ALARM(\"${aws_cloudwatch_metric_alarm.burn["${k}-short"].alarm_name}\"))"
  ])
}
