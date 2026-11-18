###############################################################################
# 第 12 讲实验 12-4：一个“配置合规”的数据桶——四层控制 + 可选的威胁检测
#   客户托管 KMS 密钥：显式密钥策略（管理员不能解密、使用者只能经 S3 使用）、每年自动轮换
#   S3 桶：四项 BPA、ACL 失效、默认 SSE-KMS + Bucket Key、阻止 SSE-C、只接受 TLS 1.2+
#   可选：GuardDuty 检测器 + S3 保护（enable_guardduty = true；新开通有 30 天试用）
# 费用：KMS 密钥 1 美元/月（按小时分摊）+ 请求费；S3 按量；GuardDuty 试用期后按事件量计费。
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
    tags = { Course = "cloudops-A06-02", Chapter = "A06-02", ManagedBy = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "bucket_name" {
  description = "实验桶名（全球唯一），以 a12- 开头。"
  type        = string
  validation {
    condition     = can(regex("^a12-[a-z0-9-]{3,59}$", var.bucket_name))
    error_message = "桶名必须以 a12- 开头，只含小写字母、数字和连字符。"
  }
}

variable "key_admin_arns" {
  description = "密钥管理员（能改策略、轮换、计划删除，但不能加解密）。为空时使用当前调用者。"
  type        = list(string)
  default     = []
}

variable "key_user_arns" {
  description = "数据读写者（只能经由 S3 使用密钥）。"
  type        = list(string)
  default     = []
}

variable "enable_guardduty" {
  description = "true 才开启 GuardDuty 与 S3 保护（试用期后产生费用；账户中已有检测器时不要开）。"
  type        = bool
  default     = false
}

data "aws_caller_identity" "current" {}

locals {
  account = data.aws_caller_identity.current.account_id
  admins  = length(var.key_admin_arns) > 0 ? var.key_admin_arns : [data.aws_caller_identity.current.arn]
  key_policy_statements = concat(
    [{
      Sid       = "EnableIAMPolicies" # 委托给本账户 IAM：防止密钥被“锁死”，也让身份策略可以授权
      Effect    = "Allow"
      Principal = { AWS = "arn:aws:iam::${local.account}:root" }
      Action    = "kms:*"
      Resource  = "*"
      },
      {
        Sid       = "KeyAdministrators" # 管理面：没有 Encrypt / Decrypt / GenerateDataKey
        Effect    = "Allow"
        Principal = { AWS = local.admins }
        Action = ["kms:Create*", "kms:Describe*", "kms:Enable*", "kms:List*", "kms:Put*", "kms:Update*",
          "kms:Revoke*", "kms:Disable*", "kms:Get*", "kms:Delete*", "kms:TagResource", "kms:UntagResource",
        "kms:ScheduleKeyDeletion", "kms:CancelKeyDeletion", "kms:RotateKeyOnDemand"]
        Resource = "*"
    }],
    length(var.key_user_arns) == 0 ? [] : [{
      Sid       = "DataUsersThroughS3Only" # 数据面：只能经 S3 在本账户内使用
      Effect    = "Allow"
      Principal = { AWS = var.key_user_arns }
      Action    = ["kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*", "kms:GenerateDataKey*", "kms:DescribeKey"]
      Resource  = "*"
      Condition = {
        StringEquals = {
          "kms:ViaService"    = "s3.${var.region}.amazonaws.com"
          "kms:CallerAccount" = local.account
        }
      }
    }]
  )
}

# ----------------------------------------------------------------------------- KMS
resource "aws_kms_key" "data" {
  description             = "A12 lab data key for S3 SSE-KMS"
  deletion_window_in_days = 7 # 计划删除期间不收月费，但密钥不可用（第 07 讲）
  enable_key_rotation     = true
  rotation_period_in_days = 365
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = local.key_policy_statements
  })
}

resource "aws_kms_alias" "data" {
  name          = "alias/a12-${var.bucket_name}"
  target_key_id = aws_kms_key.data.key_id
}

# ----------------------------------------------------------------------------- S3
resource "aws_s3_bucket" "data" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data.arn
    }
    bucket_key_enabled       = true      # 减少 KMS 请求（与费用）；不改变授权要求
    blocked_encryption_types = ["SSE-C"] # 2026-04 起新桶默认如此，这里显式写出
  }
}

resource "aws_s3_bucket_policy" "data" {
  bucket = aws_s3_bucket.data.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource  = [aws_s3_bucket.data.arn, "${aws_s3_bucket.data.arn}/*"]
        Condition = { Bool = { "aws:SecureTransport" = "false" } }
      },
      {
        Sid       = "DenyTlsOlderThan12"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource  = [aws_s3_bucket.data.arn, "${aws_s3_bucket.data.arn}/*"]
        Condition = { NumericLessThan = { "s3:TlsVersion" = "1.2" } }
      },
    ]
  })
  depends_on = [aws_s3_bucket_public_access_block.data]
}

# ----------------------------------------------------------------------------- GuardDuty（可选）
resource "aws_guardduty_detector" "this" {
  count                        = var.enable_guardduty ? 1 : 0
  enable                       = true
  finding_publishing_frequency = "FIFTEEN_MINUTES"
}

resource "aws_guardduty_detector_feature" "s3" {
  count       = var.enable_guardduty ? 1 : 0
  detector_id = aws_guardduty_detector.this[0].id
  name        = "S3_DATA_EVENTS" # S3 保护：GuardDuty 用自己的数据流分析对象级 API，不需要你建跟踪
  status      = "ENABLED"
}

# ----------------------------------------------------------------------------- 输出
output "bucket_name" {
  value = aws_s3_bucket.data.id
}

output "kms_key_arn" {
  value = aws_kms_key.data.arn
}

output "detector_id" {
  value = one(aws_guardduty_detector.this[*].id)
}
