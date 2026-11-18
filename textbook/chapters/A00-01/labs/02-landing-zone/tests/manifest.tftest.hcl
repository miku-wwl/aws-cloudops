# 用 mock provider 在本地验证 manifest 生成逻辑与依赖检查：不调用 AWS、不产生费用。
#   terraform init -backend=false
#   terraform test
mock_provider "aws" {
  # mock 默认会给 json 属性生成随机字符串；IAM 角色会校验信任策略是否为合法 JSON。
  mock_data "aws_iam_policy_document" {
    defaults = {
      json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}"
    }
  }
}

variables {
  governed_regions = ["us-east-1", "us-west-2"]
  integration_accounts = {
    logging        = "222222222222"
    security_roles = "333333333333"
    config         = "444444444444"
  }
}

run "full_governance_manifest" {
  command = plan

  assert {
    condition     = jsondecode(aws_controltower_landing_zone.this.manifest_json).config.accountId == "444444444444"
    error_message = "config 集成必须指向专用的 Config 账户。"
  }
  assert {
    condition     = jsondecode(aws_controltower_landing_zone.this.manifest_json).centralizedLogging.configurations.loggingBucket.retentionDays == 365
    error_message = "日志桶保留期应为 365 天。"
  }
  assert {
    condition     = !can(jsondecode(aws_controltower_landing_zone.this.manifest_json).backup.configurations)
    error_message = "未启用的 backup 集成不应携带 configurations。"
  }
  assert {
    condition     = !can(jsondecode(aws_controltower_landing_zone.this.manifest_json).config.configurations.kmsKeyArn)
    error_message = "未提供 kms_key_arn 时不应输出 kmsKeyArn。"
  }
  assert {
    condition     = aws_controltower_landing_zone.this.remediation_types == toset(["INHERITANCE_DRIFT"])
    error_message = "默认应开启自动账户注册（INHERITANCE_DRIFT）。"
  }
}

run "identity_center_requires_security_roles" {
  command = plan
  variables {
    integrations = {
      config              = true
      centralized_logging = true
      security_roles      = false
      access_management   = true
      backup              = false
    }
  }
  expect_failures = [aws_controltower_landing_zone.this]
}

run "security_roles_requires_config" {
  command = plan
  variables {
    integrations = {
      config              = false
      centralized_logging = true
      security_roles      = true
      access_management   = false
      backup              = false
    }
  }
  expect_failures = [aws_controltower_landing_zone.this]
}

run "enabled_integration_needs_account_id" {
  command = plan
  variables {
    integration_accounts = { logging = "222222222222", security_roles = "333333333333" }
  }
  expect_failures = [aws_controltower_landing_zone.this]
}

run "minimal_landing_zone" {
  command = plan
  variables {
    integrations = {
      config              = false
      centralized_logging = false
      security_roles      = false
      access_management   = false
      backup              = false
    }
    integration_accounts = {}
  }

  assert {
    condition = alltrue([
      for k in ["config", "centralizedLogging", "securityRoles", "accessManagement", "backup"] :
      jsondecode(aws_controltower_landing_zone.this.manifest_json)[k].enabled == false
    ])
    error_message = "最小 Landing Zone：所有集成都应为 enabled=false。"
  }
}
