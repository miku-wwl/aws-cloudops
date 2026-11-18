# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {
  override_during = plan

  mock_resource "aws_dynamodb_table" {
    defaults = { arn = "arn:aws:dynamodb:us-east-1:111122223333:table/a13-lab01-orders" }
  }

  mock_data "aws_iam_policy_document" {
    defaults = { json = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"backup.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}" }
  }
}

run "selection_is_exact_and_daily" {
  command = plan

  assert {
    condition     = aws_backup_selection.orders.resources == toset(["arn:aws:dynamodb:us-east-1:111122223333:table/a13-lab01-orders"])
    error_message = "按 ARN 精确选择这一张表。"
  }

  assert {
    condition = (
      one(aws_backup_plan.daily.rule).schedule == "cron(0 5 ? * * *)" &&
      one(one(aws_backup_plan.daily.rule).lifecycle).delete_after == 7 &&
      one(aws_backup_plan.daily.rule).start_window == 60
    )
    error_message = "每日 05:00、保留 7 天、启动窗口 60 分钟。"
  }
}

run "backup_and_restore_roles_are_separate" {
  command = plan

  assert {
    condition = (
      aws_iam_role_policy_attachment.backup.policy_arn == "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup" &&
      aws_iam_role_policy_attachment.restore.policy_arn == "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores" &&
      aws_iam_role.backup.name != aws_iam_role.restore.name
    )
    error_message = "备份与恢复使用两个角色、两份托管策略。"
  }
}

run "pitr_off_by_default" {
  command = plan

  assert {
    condition     = one(aws_dynamodb_table.orders.point_in_time_recovery).enabled == false
    error_message = "默认不开 PITR。"
  }
}

run "pitr_window_is_configurable" {
  command = plan
  variables {
    enable_pitr = true
    pitr_days   = 14
  }

  assert {
    condition     = one(aws_dynamodb_table.orders.point_in_time_recovery).recovery_period_in_days == 14
    error_message = "PITR 保留期可配置。"
  }
}

run "pitr_window_is_validated" {
  command = plan
  variables {
    enable_pitr = true
    pitr_days   = 60
  }
  expect_failures = [var.pitr_days]
}
