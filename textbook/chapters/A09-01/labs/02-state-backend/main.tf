###############################################################################
# 第 15 讲实验 15-2：远程状态的“引导（bootstrap）”工程——先单独建好状态桶，再让其他工程用它
#   私有桶 + 版本控制 + 默认加密 + ACL 失效 + 只接受 TLS + 旧版本 30 天后过期
#   输出一份最小权限的状态访问策略（只能读写某个环境的 key 与它的 .tflock）
# 本工程自己用本地状态（不能把状态桶放在它自己的后端里创建）。
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
    tags = { Course = "cloudops-A09-01", Chapter = "A09-01", ManagedBy = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "bucket_name" {
  type = string
  validation {
    condition     = can(regex("^a15-[a-z0-9-]{3,59}$", var.bucket_name))
    error_message = "桶名以 a15- 开头。"
  }
}

variable "state_prefix" {
  description = "某个环境的状态路径前缀，例如 platform/dev"
  type        = string
  default     = "platform/dev"
}

resource "aws_s3_bucket" "state" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration {
    status = "Enabled" # 状态被误删、写坏时可以回滚到上一个版本
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    id     = "expire-old-state-versions"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

resource "aws_s3_bucket_policy" "state" {
  bucket = aws_s3_bucket.state.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = [aws_s3_bucket.state.arn, "${aws_s3_bucket.state.arn}/*"]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
  depends_on = [aws_s3_bucket_public_access_block.state]
}

locals {
  key = "${var.state_prefix}/terraform.tfstate"
  state_access_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "ListOnlyThisEnvironment"
        Effect    = "Allow"
        Action    = "s3:ListBucket"
        Resource  = "arn:aws:s3:::${var.bucket_name}"
        Condition = { StringLike = { "s3:prefix" = ["${var.state_prefix}/*"] } }
      },
      {
        Sid      = "ReadWriteState"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "arn:aws:s3:::${var.bucket_name}/${local.key}"
      },
      {
        Sid      = "LockFile"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        Resource = "arn:aws:s3:::${var.bucket_name}/${local.key}.tflock"
      },
    ]
  })
}

output "backend_block" {
  value = <<-EOT
    terraform {
      backend "s3" {
        bucket       = "${var.bucket_name}"
        key          = "${local.key}"
        region       = "${var.region}"
        encrypt      = true
        use_lockfile = true   # S3 原生锁：<key>.tflock；DynamoDB 锁已弃用
      }
    }
  EOT
}

output "state_access_policy" {
  value = local.state_access_policy
}
