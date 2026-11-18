###############################################################################
# 第 11 讲实验 11-4：一个空桶上的“行为证据”与“状态证据”
#   Part A（默认，几乎零费用）：一个空的私有桶——Owner 等标签、四项公共访问阻止、
#          对象所有权强制归桶主（ACL 失效）、默认加密。CloudTrail 事件历史无需配置即可追溯。
#   Part B（enable_config = true，按配置项与规则评估计费）：只记录 AWS::S3::Bucket 的
#          客户托管配置记录器（使用已有的服务关联角色 AWSServiceRoleForConfig）、专用投递桶、
#          托管规则 S3_BUCKET_TAGGED（requiredKeyTags = Owner），范围只限实验桶。
# 前提：一个账户的一个区域只能有一个客户托管配置记录器——先运行 scripts/preflight.sh。
###############################################################################
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = { Course = "cloudops-A06-01", ManagedBy = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "bucket_name" {
  description = "实验桶名（全球唯一），必须以 a11- 开头。"
  type        = string
  validation {
    condition     = can(regex("^a11-[a-z0-9-]{3,59}$", var.bucket_name))
    error_message = "桶名必须以 a11- 开头，只含小写字母、数字和连字符，总长 ≤ 63。"
  }
}

variable "enable_config" {
  description = "true 才启用 AWS Config（产生配置项与规则评估费用）。"
  type        = bool
  default     = false
}

variable "config_bucket_name" {
  description = "Config 投递桶名（全球唯一）；enable_config = true 时必填。"
  type        = string
  default     = ""
  validation {
    condition     = !var.enable_config || can(regex("^a11-[a-z0-9-]{3,59}$", var.config_bucket_name))
    error_message = "启用 Config 时必须提供以 a11- 开头的投递桶名。"
  }
}

data "aws_caller_identity" "current" {}

locals {
  account = data.aws_caller_identity.current.account_id
  slr_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig"
  config  = var.enable_config ? 1 : 0
  owner_tags = {
    Project     = "aws-cloudops"
    Environment = "sandbox"
    Owner       = "cloudops-lab"
    Chapter     = "A06-01"
  }
}

# ============================================================================ Part A：空的私有桶
resource "aws_s3_bucket" "lab" {
  bucket = var.bucket_name
  tags   = local.owner_tags # 这四个标签就是“基线”：PutBucketTagging 会整体替换它们
}

resource "aws_s3_bucket_public_access_block" "lab" {
  bucket                  = aws_s3_bucket.lab.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "lab" {
  bucket = aws_s3_bucket.lab.id
  rule {
    object_ownership = "BucketOwnerEnforced" # ACL 一律失效，权限只看策略
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lab" {
  bucket = aws_s3_bucket.lab.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ============================================================================ Part B：AWS Config（可选）
resource "aws_s3_bucket" "config_logs" {
  count         = local.config
  bucket        = var.config_bucket_name
  force_destroy = true # 只用于实验：destroy 时连同 Config 写入的历史文件一起删除
}

resource "aws_s3_bucket_public_access_block" "config_logs" {
  count                   = local.config
  bucket                  = aws_s3_bucket.config_logs[0].id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "config_logs" {
  count  = local.config
  bucket = aws_s3_bucket.config_logs[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AWSConfigBucketPermissionsCheck"
        Effect    = "Allow"
        Principal = { Service = "config.amazonaws.com" }
        Action    = "s3:GetBucketAcl"
        Resource  = aws_s3_bucket.config_logs[0].arn
        Condition = { StringEquals = { "aws:SourceAccount" = local.account } }
      },
      {
        Sid       = "AWSConfigBucketExistenceCheck"
        Effect    = "Allow"
        Principal = { Service = "config.amazonaws.com" }
        Action    = "s3:ListBucket"
        Resource  = aws_s3_bucket.config_logs[0].arn
        Condition = { StringEquals = { "aws:SourceAccount" = local.account } }
      },
      {
        Sid       = "AWSConfigBucketDelivery"
        Effect    = "Allow"
        Principal = { Service = "config.amazonaws.com" }
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.config_logs[0].arn}/AWSLogs/${local.account}/Config/*"
        Condition = { StringEquals = { "s3:x-amz-acl" = "bucket-owner-full-control", "aws:SourceAccount" = local.account } }
      },
    ]
  })
}

resource "aws_config_configuration_recorder" "this" {
  count    = local.config
  name     = "a11-recorder"
  role_arn = local.slr_arn # 账户已有的服务关联角色 AWSServiceRoleForConfig

  recording_group {
    all_supported                 = false
    include_global_resource_types = false
    resource_types                = ["AWS::S3::Bucket"] # 仍会记录本区域“所有”桶，不只是实验桶
    recording_strategy {
      use_only = "INCLUSION_BY_RESOURCE_TYPES"
    }
  }

  recording_mode {
    recording_frequency = "CONTINUOUS" # 每次变化一个配置项；DAILY 更便宜但最多延迟一天
  }
}

resource "aws_config_delivery_channel" "this" {
  count          = local.config
  name           = "a11-channel"
  s3_bucket_name = aws_s3_bucket.config_logs[0].id
  depends_on     = [aws_config_configuration_recorder.this, aws_s3_bucket_policy.config_logs]
}

resource "aws_config_configuration_recorder_status" "this" {
  count      = local.config
  name       = aws_config_configuration_recorder.this[0].name
  is_enabled = true
  depends_on = [aws_config_delivery_channel.this]
}

resource "aws_config_config_rule" "owner_tag" {
  count            = local.config
  name             = "a11-s3-requires-owner-tag"
  description      = "Lab bucket must carry an Owner tag (S3_BUCKET_TAGGED, requiredKeyTags=Owner)"
  input_parameters = jsonencode({ requiredKeyTags = "Owner" })

  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_TAGGED"
  }

  scope {
    compliance_resource_types = ["AWS::S3::Bucket"]
    compliance_resource_id    = aws_s3_bucket.lab.bucket # 只评估实验桶（桶名在 plan 时已知）
  }

  depends_on = [aws_config_configuration_recorder_status.this]
}

# ============================================================================ 输出
output "bucket_name" {
  value = aws_s3_bucket.lab.id
}

output "config_rule_name" {
  value = one(aws_config_config_rule.owner_tag[*].name)
}
