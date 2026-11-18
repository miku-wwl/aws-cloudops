# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {
  override_during = plan

  mock_data "aws_caller_identity" {
    defaults = { account_id = "111122223333", arn = "arn:aws:iam::111122223333:user/ops-admin" }
  }

  mock_resource "aws_kms_key" {
    defaults = { arn = "arn:aws:kms:us-east-1:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab", key_id = "1234abcd-12ab-34cd-56ef-1234567890ab" }
  }

  mock_resource "aws_s3_bucket" {
    defaults = { arn = "arn:aws:s3:::a12-lab01-data", id = "a12-lab01-data" }
  }
}

variables {
  bucket_name   = "a12-lab01-data"
  key_user_arns = ["arn:aws:iam::111122223333:role/a12-app"]
}

run "key_policy_separates_admins_from_users" {
  command = plan

  assert {
    condition = alltrue([for s in jsondecode(aws_kms_key.data.policy).Statement :
    !contains(flatten([s.Action]), "kms:Decrypt") if s.Sid == "KeyAdministrators"])
    error_message = "密钥管理员不应有 kms:Decrypt。"
  }

  assert {
    condition = one([for s in jsondecode(aws_kms_key.data.policy).Statement :
    s.Condition.StringEquals["kms:ViaService"] if s.Sid == "DataUsersThroughS3Only"]) == "s3.us-east-1.amazonaws.com"
    error_message = "数据使用者只能经由 S3 使用密钥。"
  }

  assert {
    condition     = aws_kms_key.data.enable_key_rotation && aws_kms_key.data.rotation_period_in_days == 365
    error_message = "启用每年自动轮换。"
  }
}

run "bucket_has_four_layers" {
  command = plan

  assert {
    condition = (
      aws_s3_bucket_public_access_block.data.block_public_acls && aws_s3_bucket_public_access_block.data.restrict_public_buckets &&
      one(aws_s3_bucket_ownership_controls.data.rule).object_ownership == "BucketOwnerEnforced"
    )
    error_message = "BPA 与 ACL 失效。"
  }

  assert {
    condition = (
      one(one(aws_s3_bucket_server_side_encryption_configuration.data.rule).apply_server_side_encryption_by_default).sse_algorithm == "aws:kms" &&
      one(aws_s3_bucket_server_side_encryption_configuration.data.rule).bucket_key_enabled &&
      contains(one(aws_s3_bucket_server_side_encryption_configuration.data.rule).blocked_encryption_types, "SSE-C")
    )
    error_message = "默认 SSE-KMS + Bucket Key，并阻止 SSE-C。"
  }

  assert {
    condition = (
      contains([for s in jsondecode(aws_s3_bucket_policy.data.policy).Statement : s.Sid], "DenyInsecureTransport") &&
      contains([for s in jsondecode(aws_s3_bucket_policy.data.policy).Statement : s.Sid], "DenyTlsOlderThan12")
    )
    error_message = "桶策略拒绝非 TLS 与 TLS 1.2 以下的请求。"
  }
}

run "guardduty_is_opt_in" {
  command = plan

  assert {
    condition     = length(aws_guardduty_detector.this) == 0
    error_message = "默认不开 GuardDuty。"
  }
}

run "guardduty_with_s3_protection" {
  command = plan
  variables {
    enable_guardduty = true
  }

  assert {
    condition     = aws_guardduty_detector_feature.s3[0].name == "S3_DATA_EVENTS" && aws_guardduty_detector_feature.s3[0].status == "ENABLED"
    error_message = "开启 S3 保护。"
  }
}
