# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {}

run "default_creates_nothing" {
  command = plan

  assert {
    condition     = length(aws_cloudwatch_log_group.lab) == 0 && length(aws_budgets_budget.lab) == 0 && length(aws_ce_cost_allocation_tag.project) == 0
    error_message = "enable = false 时不应创建任何资源。"
  }
}

run "log_group_has_finite_retention" {
  command = plan
  variables { enable = true }

  assert {
    condition     = aws_cloudwatch_log_group.lab[0].retention_in_days == 7
    error_message = "日志组必须有有限的保留期。"
  }

  assert {
    condition     = length(aws_budgets_budget.lab) == 0
    error_message = "没有通知邮箱时不创建预算。"
  }
}

run "budget_filters_by_activated_tag_and_forecasts" {
  command = plan
  variables {
    enable       = true
    notify_email = "ops@example.invalid"
  }

  assert {
    condition     = aws_ce_cost_allocation_tag.project[0].status == "Active" && aws_ce_cost_allocation_tag.project[0].tag_key == "Project"
    error_message = "预算按标签过滤，前提是该标签已激活为成本分摊标签。"
  }

  assert {
    condition     = one([for f in aws_budgets_budget.lab[0].cost_filter : f.values[0] if f.name == "TagKeyValue"]) == "user:Project$finops-lab"
    error_message = "预算应只统计 Project=finops-lab 的费用。"
  }

  assert {
    condition     = contains([for n in aws_budgets_budget.lab[0].notification : n.notification_type], "FORECASTED")
    error_message = "除了实际花费，还要对“预测将超支”报警。"
  }
}

run "expires_on_format_is_checked" {
  command = plan
  variables { expires_on = "next week" }
  expect_failures = [var.expires_on]
}
