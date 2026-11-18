# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {
  override_during = plan

  mock_resource "aws_s3_bucket" {
    defaults = { arn = "arn:aws:s3:::a15-lab01-state", id = "a15-lab01-state" }
  }
}

variables {
  bucket_name = "a15-lab01-state"
}

run "state_bucket_is_versioned_private_and_tls_only" {
  command = plan

  assert {
    condition     = one(aws_s3_bucket_versioning.state.versioning_configuration).status == "Enabled"
    error_message = "状态桶必须开版本控制。"
  }

  assert {
    condition     = aws_s3_bucket_public_access_block.state.restrict_public_buckets && aws_s3_bucket_public_access_block.state.block_public_policy
    error_message = "状态桶必须阻止公开访问。"
  }

  assert {
    condition     = jsondecode(aws_s3_bucket_policy.state.policy).Statement[0].Condition.Bool["aws:SecureTransport"] == "false"
    error_message = "拒绝非 TLS 请求。"
  }
}

run "access_policy_covers_key_and_lockfile_only" {
  command = plan

  assert {
    condition = (
      jsondecode(output.state_access_policy).Statement[1].Resource == "arn:aws:s3:::a15-lab01-state/platform/dev/terraform.tfstate" &&
      jsondecode(output.state_access_policy).Statement[2].Resource == "arn:aws:s3:::a15-lab01-state/platform/dev/terraform.tfstate.tflock" &&
      !contains(jsondecode(output.state_access_policy).Statement[1].Action, "s3:DeleteObject")
    )
    error_message = "只能读写本环境的状态，删除权限只给 .tflock。"
  }

  assert {
    condition     = strcontains(output.backend_block, "use_lockfile = true")
    error_message = "后端使用 S3 原生锁。"
  }
}
