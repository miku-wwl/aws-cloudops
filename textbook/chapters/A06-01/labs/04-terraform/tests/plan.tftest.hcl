# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {
  override_during = plan

  mock_data "aws_caller_identity" {
    defaults = { account_id = "111122223333" }
  }

  mock_resource "aws_s3_bucket" {
    defaults = { arn = "arn:aws:s3:::a11-lab01-config" }
  }
}

variables {
  bucket_name = "a11-lab01-demo"
}

run "part_a_is_private_and_tagged" {
  command = plan

  assert {
    condition = (
      aws_s3_bucket_public_access_block.lab.block_public_acls && aws_s3_bucket_public_access_block.lab.ignore_public_acls &&
      aws_s3_bucket_public_access_block.lab.block_public_policy && aws_s3_bucket_public_access_block.lab.restrict_public_buckets
    )
    error_message = "四项公共访问阻止必须全部开启。"
  }

  assert {
    condition     = one(aws_s3_bucket_ownership_controls.lab.rule).object_ownership == "BucketOwnerEnforced"
    error_message = "对象所有权强制归桶主（ACL 失效）。"
  }

  assert {
    condition     = aws_s3_bucket.lab.tags["Owner"] == "cloudops-lab"
    error_message = "基线必须带 Owner 标签。"
  }
}

run "config_is_opt_in" {
  command = plan

  assert {
    condition     = length(aws_config_configuration_recorder.this) == 0 && length(aws_config_config_rule.owner_tag) == 0
    error_message = "默认不启用 Config。"
  }
}

run "config_needs_a_delivery_bucket" {
  command = plan
  variables {
    enable_config = true
  }
  expect_failures = [var.config_bucket_name]
}

run "config_records_only_buckets_with_the_slr" {
  command = plan
  variables {
    enable_config      = true
    config_bucket_name = "a11-lab01-config"
  }

  assert {
    condition = (
      one(aws_config_configuration_recorder.this[0].recording_group).resource_types == toset(["AWS::S3::Bucket"]) &&
      one(aws_config_configuration_recorder.this[0].recording_mode).recording_frequency == "CONTINUOUS" &&
      endswith(aws_config_configuration_recorder.this[0].role_arn, "role/aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig")
    )
    error_message = "记录器：只记录 S3 桶、连续记录、使用服务关联角色。"
  }

  assert {
    condition = (
      one(aws_config_config_rule.owner_tag[0].source).source_identifier == "S3_BUCKET_TAGGED" &&
      jsondecode(aws_config_config_rule.owner_tag[0].input_parameters).requiredKeyTags == "Owner" &&
      one(aws_config_config_rule.owner_tag[0].scope).compliance_resource_id == "a11-lab01-demo"
    )
    error_message = "规则：S3_BUCKET_TAGGED，requiredKeyTags=Owner，只评估实验桶。"
  }

  assert {
    condition = alltrue([for s in jsondecode(aws_s3_bucket_policy.config_logs[0].policy).Statement :
    s.Condition.StringEquals["aws:SourceAccount"] == "111122223333"])
    error_message = "投递桶策略的每条语句都要限定 aws:SourceAccount（防混淆代理）。"
  }
}

run "bucket_name_is_validated" {
  command = plan
  variables {
    bucket_name = "My_Bucket"
  }
  expect_failures = [var.bucket_name]
}
