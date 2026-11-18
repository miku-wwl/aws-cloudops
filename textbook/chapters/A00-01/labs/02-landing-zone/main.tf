###############################################################################
# A00-01 实验 3：用 Terraform 描述 Control Tower Landing Zone 4.0
#
# 前置条件（不在本模块中创建，见教材 6.1 节）：
#   1. 已有 AWS Organizations 组织（ALL features），本账户为管理账户；
#   2. 已为启用的集成准备好账户，并放在同一个根级 OU（Security OU）下；
#   3. 执行身份具备 controltower:*LandingZone*、organizations:*、iam:*Role* 等权限。
# 本模块只在 `terraform plan/test` 中做静态验证；apply 会真实创建 Landing Zone
# 并持续产生 CloudTrail/Config/S3 等费用，请在专用沙箱组织中执行。
###############################################################################

locals {
  sw   = var.integrations
  acct = var.integration_accounts

  # 存储桶配置。kms_key_arn 为空时不输出 kmsKeyArn 字段。
  bucket_cfg = { for k, v in {
    loggingBucket       = { retentionDays = var.log_retention_days }
    accessLoggingBucket = { retentionDays = var.access_log_retention_days }
    kmsKeyArn           = var.kms_key_arn
  } : k => v if v != null }

  # 每个集成先写成“字段齐全、未用字段为 null”的对象，再统一去掉 null，
  # 这样 Terraform 的条件表达式两侧类型一致，生成的 JSON 也不会出现 null。
  blocks = {
    config = {
      enabled        = local.sw.config
      accountId      = local.sw.config ? local.acct.config : null
      configurations = local.sw.config ? local.bucket_cfg : null
    }
    centralizedLogging = {
      enabled        = local.sw.centralized_logging
      accountId      = local.sw.centralized_logging ? local.acct.logging : null
      configurations = local.sw.centralized_logging ? local.bucket_cfg : null
    }
    securityRoles = {
      enabled   = local.sw.security_roles
      accountId = local.sw.security_roles ? local.acct.security_roles : null
    }
    accessManagement = {
      enabled = local.sw.access_management
    }
    backup = {
      enabled = local.sw.backup
      configurations = local.sw.backup ? { for k, v in {
        centralBackup = { accountId = local.acct.backup_central }
        backupAdmin   = { accountId = local.acct.backup_admin }
        kmsKeyArn     = var.kms_key_arn
      } : k => v if v != null } : null
    }
  }

  manifest = merge(
    { governedRegions = var.governed_regions },
    { for name, blk in local.blocks : name => { for k, v in blk : k => v if v != null } }
  )

  # 已启用的集成 → 必须提供的账户
  required_accounts = merge(
    local.sw.config ? { config = local.acct.config } : {},
    local.sw.centralized_logging ? { logging = local.acct.logging } : {},
    local.sw.security_roles ? { security_roles = local.acct.security_roles } : {},
    local.sw.backup ? { backup_central = local.acct.backup_central, backup_admin = local.acct.backup_admin } : {},
  )
  missing_accounts = sort([for k, v in local.required_accounts : k if v == null ? true : !can(regex("^[0-9]{12}$", v))])
}

# ---------------------------------------------------------------------------
# 1) Control Tower 服务角色（API 方式落地必须预先创建，路径为 /service-role/）
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "trust" {
  for_each = {
    admin      = "controltower.amazonaws.com"
    cloudtrail = "cloudtrail.amazonaws.com"
    stackset   = "cloudformation.amazonaws.com"
  }

  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = [each.value]
    }
  }
}

resource "aws_iam_role" "ct_admin" {
  name               = "AWSControlTowerAdmin"
  path               = "/service-role/"
  assume_role_policy = data.aws_iam_policy_document.trust["admin"].json
}

resource "aws_iam_role_policy" "ct_admin" {
  name = "AWSControlTowerAdminPolicy"
  role = aws_iam_role.ct_admin.id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "ec2:DescribeAvailabilityZones", Resource = "*" }]
  })
}

resource "aws_iam_role_policy_attachment" "ct_admin" {
  role       = aws_iam_role.ct_admin.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSControlTowerServiceRolePolicy"
}

resource "aws_iam_role" "ct_cloudtrail" {
  name               = "AWSControlTowerCloudTrailRole"
  path               = "/service-role/"
  assume_role_policy = data.aws_iam_policy_document.trust["cloudtrail"].json
}

# LZ 4.0 要求使用托管策略 AWSControlTowerCloudTrailRolePolicy（替代旧的内联策略）
resource "aws_iam_role_policy_attachment" "ct_cloudtrail" {
  role       = aws_iam_role.ct_cloudtrail.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSControlTowerCloudTrailRolePolicy"
}

resource "aws_iam_role" "ct_stackset" {
  name               = "AWSControlTowerStackSetRole"
  path               = "/service-role/"
  assume_role_policy = data.aws_iam_policy_document.trust["stackset"].json
}

resource "aws_iam_role_policy" "ct_stackset" {
  name = "AWSControlTowerStackSetRolePolicy"
  role = aws_iam_role.ct_stackset.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sts:AssumeRole"]
      Resource = ["arn:aws:iam::*:role/AWSControlTowerExecution"]
    }]
  })
}

# ---------------------------------------------------------------------------
# 2) Landing Zone 本体
# ---------------------------------------------------------------------------
resource "aws_controltower_landing_zone" "this" {
  version           = var.landing_zone_version
  manifest_json     = jsonencode(local.manifest)
  remediation_types = var.auto_enrollment ? ["INHERITANCE_DRIFT"] : null

  depends_on = [
    aws_iam_role_policy.ct_admin,
    aws_iam_role_policy_attachment.ct_admin,
    aws_iam_role_policy_attachment.ct_cloudtrail,
    aws_iam_role_policy.ct_stackset,
  ]

  lifecycle {
    # 拆除 Landing Zone 是有计划的“退役”流程，不应被一次 destroy 误触发。
    prevent_destroy = true

    precondition {
      condition     = contains(var.governed_regions, var.home_region)
      error_message = "governed_regions 必须包含 home_region。"
    }
    precondition {
      condition     = !local.sw.security_roles || local.sw.config
      error_message = "security_roles 依赖 config 集成（CentralSecurityRolesBaseline 需要 CentralConfigBaseline）。"
    }
    precondition {
      condition     = !local.sw.access_management || local.sw.security_roles
      error_message = "access_management（IAM Identity Center）依赖 security_roles 集成。"
    }
    precondition {
      condition     = !local.sw.backup || local.sw.security_roles
      error_message = "backup 依赖 security_roles 集成。"
    }
    precondition {
      condition     = length(local.missing_accounts) == 0
      error_message = "以下已启用的集成缺少有效的 12 位账户 ID：${join(", ", local.missing_accounts)}。"
    }
  }
}
