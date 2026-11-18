###############################################################################
# 第 07 讲实验 7-3：GitHub OIDC → 角色 → Secrets Manager（客户托管 KMS 密钥）
#   allow_kms_decrypt —— 故障开关：角色是否有（带条件的）kms:Decrypt
# 秘密值用 Terraform 1.11+ 的“只写参数”secret_string_wo 写入：不进 plan、不进 state。
# 费用：客户托管 KMS 密钥 1 美元/月（按小时折算，待删除期间不收费）；秘密 0.40 美元/月。
###############################################################################
terraform {
  required_version = ">= 1.11.0" # 只写参数（write-only arguments）需要 1.11+
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
    tags = { Course = "cloudops-A03-02", ManagedBy = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "github_sub_prefix" {
  description = <<-EOT
    GitHub OIDC sub 的仓库部分。两种格式：
      旧：repo:<owner>/<repo>
      新：repo:<owner>@<ownerId>/<repo>@<repoId>   （2026-07-15 之后创建 / 改名 / 转移的仓库默认使用）
    用 gh api repos/<owner>/<repo> --jq '.owner.id, .id' 查询数字 ID。
  EOT
  type        = string
  default     = "repo:example-org/cloudops-lab"

  validation {
    condition     = can(regex("^repo:[A-Za-z0-9_.-]+(@[0-9]+)?/[A-Za-z0-9_.-]+(@[0-9]+)?$", var.github_sub_prefix))
    error_message = "github_sub_prefix 形如 repo:owner/repo 或 repo:owner@123/repo@456，不能含通配符。"
  }
}

variable "github_branch" {
  type    = string
  default = "main"
}

variable "create_oidc_provider" {
  description = "账户里还没有 token.actions.githubusercontent.com 提供商时设为 true；已有则 false 并给出 ARN（不要删除共享提供商）。"
  type        = bool
  default     = true
}

variable "existing_oidc_provider_arn" {
  type    = string
  default = null
}

variable "allow_kms_decrypt" {
  description = "故障开关：false 时角色只有 GetSecretValue，没有 kms:Decrypt。"
  type        = bool
  default     = false
}

variable "demo_secret_value" {
  description = "仅用于教学的虚构值；只写参数，不会出现在 plan 与 state 中。"
  type        = string
  default     = "DEMO-NOT-A-PASSWORD"
  sensitive   = true
  ephemeral   = true
}

data "aws_caller_identity" "me" {}

# ---------------------------------------------------------------- OIDC 提供商
resource "aws_iam_openid_connect_provider" "github" {
  count          = var.create_oidc_provider ? 1 : 0
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  # 对 GitHub，IAM 使用自带的受信任根 CA 校验，不需要 thumbprint_list
}

locals {
  provider_arn = var.create_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : var.existing_oidc_provider_arn
  account_id   = data.aws_caller_identity.me.account_id
}

# ---------------------------------------------------------------- 角色：只信任指定仓库的指定分支
resource "aws_iam_role" "gh_reader" {
  name                 = "a07-gh-secret-reader"
  max_session_duration = 3600
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "GitHubMainOnly"
      Effect    = "Allow"
      Principal = { Federated = local.provider_arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          "token.actions.githubusercontent.com:sub" = "${var.github_sub_prefix}:ref:refs/heads/${var.github_branch}"
        }
      }
    }]
  })

  lifecycle {
    precondition {
      condition     = local.provider_arn != null
      error_message = "create_oidc_provider = false 时必须提供 existing_oidc_provider_arn。"
    }
  }
}

# ---------------------------------------------------------------- 客户托管 KMS 密钥
resource "aws_kms_key" "secrets" {
  description             = "a07 lab key for one secret"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      # 让本账户的 IAM 策略能够授权使用这把密钥（否则任何 IAM Allow 都不生效）
      Sid       = "EnableIAMPolicies"
      Effect    = "Allow"
      Principal = { AWS = "arn:aws:iam::${local.account_id}:root" }
      Action    = "kms:*"
      Resource  = "*"
    }]
  })
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/a07-lab-secrets"
  target_key_id = aws_kms_key.secrets.key_id
}

# ---------------------------------------------------------------- 秘密
resource "aws_secretsmanager_secret" "demo" {
  name_prefix             = "a07/demo-"
  kms_key_id              = aws_kms_key.secrets.arn
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "demo" {
  secret_id                = aws_secretsmanager_secret.demo.id
  secret_string_wo         = var.demo_secret_value # 只写：不进 state
  secret_string_wo_version = 1                     # 改值时把版本号加 1
}

# ---------------------------------------------------------------- 角色权限
locals {
  reader_statements = concat(
    [{
      Sid      = "ReadThisSecret"
      Effect   = "Allow"
      Action   = "secretsmanager:GetSecretValue"
      Resource = aws_secretsmanager_secret.demo.arn
    }],
    var.allow_kms_decrypt ? [{
      Sid      = "DecryptOnlyViaSecretsManagerForThisSecret"
      Effect   = "Allow"
      Action   = "kms:Decrypt"
      Resource = aws_kms_key.secrets.arn
      Condition = {
        StringEquals = {
          "kms:ViaService"                  = "secretsmanager.${var.region}.amazonaws.com"
          "kms:EncryptionContext:SecretARN" = aws_secretsmanager_secret.demo.arn
        }
      }
    }] : []
  )
}

resource "aws_iam_role_policy" "gh_reader" {
  name   = "a07-read-one-secret"
  role   = aws_iam_role.gh_reader.id
  policy = jsonencode({ Version = "2012-10-17", Statement = local.reader_statements })
}

output "role_arn" {
  value = aws_iam_role.gh_reader.arn
}

output "secret_arn" {
  value = aws_secretsmanager_secret.demo.arn
}

output "kms_key_arn" {
  value = aws_kms_key.secrets.arn
}
