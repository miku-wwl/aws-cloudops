###############################################################################
# 第 06 讲实验 6-2：用 STS 换身份，再让角色会话读取两个对象
#   allow_report    —— 修复开关：给 reports/summary.csv 加一条精确 Allow
#   enable_boundary —— 给角色挂权限边界（只允许 logs/*），观察“边界只设上限”
# 资源：1 个私有桶 + 2 个对象 + 桶策略（拒绝非 HTTPS）+ 1 个角色（+ 可选边界策略）。
# 费用：S3 存储与请求可忽略；IAM 与 STS 不收费。
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
    tags = { Course = "cloudops-A03-01", ManagedBy = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "operator_arn" {
  description = "允许扮演角色的 IAM 用户或角色 ARN（不能是 sts::…:assumed-role/… 会话 ARN）。"
  type        = string

  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:(user|role)/.+$", var.operator_arn))
    error_message = "operator_arn 必须是 IAM 用户或角色的 ARN（arn:aws:iam::<账户>:user/… 或 :role/…），不能是临时会话 ARN。"
  }
}

variable "allow_report" {
  description = "修复开关：是否允许读取 reports/summary.csv。"
  type        = bool
  default     = false
}

variable "enable_boundary" {
  description = "是否为角色设置只允许 logs/* 的权限边界。"
  type        = bool
  default     = false
}

# ---------------------------------------------------------------- 桶与两个对象
resource "aws_s3_bucket" "lab" {
  bucket_prefix = "a06-iam-sts-lab-"
  force_destroy = true # 专用实验桶：destroy 时连同对象一起删除
}

resource "aws_s3_bucket_public_access_block" "lab" {
  bucket                  = aws_s3_bucket.lab.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "tls_only" {
  bucket = aws_s3_bucket.lab.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = [aws_s3_bucket.lab.arn, "${aws_s3_bucket.lab.arn}/*"]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
  depends_on = [aws_s3_bucket_public_access_block.lab]
}

resource "aws_s3_object" "health" {
  bucket  = aws_s3_bucket.lab.id
  key     = "logs/health.txt"
  content = "ok\n"
}

resource "aws_s3_object" "report" {
  bucket  = aws_s3_bucket.lab.id
  key     = "reports/summary.csv"
  content = "period,total\n2026-11,42\n"
}

# ---------------------------------------------------------------- 角色：信任策略 + 权限策略
locals {
  trust_policy = {
    Version = "2012-10-17"
    Statement = [{
      Sid       = "OnlyApprovedOperator"
      Effect    = "Allow"
      Principal = { AWS = var.operator_arn }
      Action    = ["sts:AssumeRole", "sts:TagSession"]
    }]
  }

  reader_statements = concat(
    [{
      Sid      = "ReadHealthOnly"
      Effect   = "Allow"
      Action   = "s3:GetObject"
      Resource = "${aws_s3_bucket.lab.arn}/${aws_s3_object.health.key}"
    }],
    var.allow_report ? [{
      Sid      = "ReadReportAfterFix"
      Effect   = "Allow"
      Action   = "s3:GetObject"
      Resource = "${aws_s3_bucket.lab.arn}/${aws_s3_object.report.key}"
    }] : []
  )
}

resource "aws_iam_role" "reader" {
  name                 = "a06-sts-reader"
  assume_role_policy   = jsonencode(local.trust_policy)
  max_session_duration = 3600
  permissions_boundary = var.enable_boundary ? aws_iam_policy.boundary[0].arn : null
}

resource "aws_iam_role_policy" "reader" {
  name   = "a06-s3-object-reader"
  role   = aws_iam_role.reader.id
  policy = jsonencode({ Version = "2012-10-17", Statement = local.reader_statements })
}

# 权限边界：一个“上限”。它本身不授予任何权限
resource "aws_iam_policy" "boundary" {
  count = var.enable_boundary ? 1 : 0
  name  = "a06-boundary-logs-only"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "BoundaryLogsOnly"
      Effect   = "Allow"
      Action   = "s3:GetObject"
      Resource = "${aws_s3_bucket.lab.arn}/logs/*"
    }]
  })
}

output "reader_role_arn" {
  value = aws_iam_role.reader.arn
}

output "lab_bucket" {
  value = aws_s3_bucket.lab.id
}
