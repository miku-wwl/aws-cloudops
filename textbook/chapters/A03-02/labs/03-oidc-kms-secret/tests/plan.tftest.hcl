# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {
  override_during = plan
  mock_data "aws_caller_identity" {
    defaults = { account_id = "111122223333" }
  }
  mock_resource "aws_iam_openid_connect_provider" {
    defaults = { arn = "arn:aws:iam::111122223333:oidc-provider/token.actions.githubusercontent.com" }
  }
  mock_resource "aws_kms_key" {
    defaults = { arn = "arn:aws:kms:us-east-1:111122223333:key/11111111-2222-3333-4444-555555555555", key_id = "11111111-2222-3333-4444-555555555555" }
  }
  mock_resource "aws_secretsmanager_secret" {
    defaults = { arn = "arn:aws:secretsmanager:us-east-1:111122223333:secret:a07/demo-AbCdEf", id = "arn:aws:secretsmanager:us-east-1:111122223333:secret:a07/demo-AbCdEf" }
  }
}

run "trust_pins_repo_and_branch" {
  command = plan

  assert {
    condition     = jsondecode(aws_iam_role.gh_reader.assume_role_policy).Statement[0].Condition.StringEquals["token.actions.githubusercontent.com:sub"] == "repo:example-org/cloudops-lab:ref:refs/heads/main"
    error_message = "sub 必须精确到仓库与分支。"
  }
  assert {
    condition     = jsondecode(aws_iam_role.gh_reader.assume_role_policy).Statement[0].Condition.StringEquals["token.actions.githubusercontent.com:aud"] == "sts.amazonaws.com"
    error_message = "aud 必须是 sts.amazonaws.com。"
  }
}

run "new_immutable_sub_format" {
  command = plan
  variables {
    github_sub_prefix = "repo:example-org@1234/cloudops-lab@5678"
  }

  assert {
    condition     = jsondecode(aws_iam_role.gh_reader.assume_role_policy).Statement[0].Condition.StringEquals["token.actions.githubusercontent.com:sub"] == "repo:example-org@1234/cloudops-lab@5678:ref:refs/heads/main"
    error_message = "新格式 sub 包含数字 ID。"
  }
}

run "reject_wildcard_subject" {
  command = plan
  variables {
    github_sub_prefix = "repo:example-org/*"
  }
  expect_failures = [var.github_sub_prefix]
}

run "fault_state_has_no_decrypt" {
  command = plan

  assert {
    condition     = length(jsondecode(aws_iam_role_policy.gh_reader.policy).Statement) == 1
    error_message = "故障态：只有 GetSecretValue。"
  }
}

run "fix_adds_scoped_decrypt" {
  command = plan
  variables {
    allow_kms_decrypt = true
  }

  assert {
    condition = (
      jsondecode(aws_iam_role_policy.gh_reader.policy).Statement[1].Action == "kms:Decrypt" &&
      jsondecode(aws_iam_role_policy.gh_reader.policy).Statement[1].Condition.StringEquals["kms:ViaService"] == "secretsmanager.us-east-1.amazonaws.com" &&
      jsondecode(aws_iam_role_policy.gh_reader.policy).Statement[1].Condition.StringEquals["kms:EncryptionContext:SecretARN"] == "arn:aws:secretsmanager:us-east-1:111122223333:secret:a07/demo-AbCdEf"
    )
    error_message = "修复只加一条 kms:Decrypt，并限定 ViaService 与 SecretARN 加密上下文。"
  }
}

run "secret_value_is_write_only" {
  command = plan

  assert {
    condition     = aws_secretsmanager_secret_version.demo.secret_string == null
    error_message = "不应使用会写入 state 的 secret_string。"
  }
}

run "key_rotation_and_deletion_window" {
  command = plan

  assert {
    condition     = aws_kms_key.secrets.enable_key_rotation && aws_kms_key.secrets.deletion_window_in_days == 7
    error_message = "实验密钥开启轮换，删除等待期 7 天（最短）。"
  }
}
