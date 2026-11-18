###############################################################################
# A00-01 实验 4：把 NonProd OU 纳入治理（OU + 基线 + 控制）
# 运行前提：Landing Zone 已 ACTIVE，且 config 集成已启用（AWSControlTowerBaseline 的前置条件）。
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
  region = var.home_region
}

variable "home_region" {
  type    = string
  default = "us-east-1"
}

variable "baseline_arn" {
  description = "AWSControlTowerBaseline 的 ARN（区域相关）。用 aws controltower list-baselines 查询。"
  type        = string
  default     = "arn:aws:controltower:us-east-1::baseline/17BSJV3IGJ2QSGA2"
}

variable "baseline_version" {
  description = "LZ 4.0 对应的 AWSControlTowerBaseline 版本为 5.0。"
  type        = string
  default     = "5.0"
}

variable "idc_baseline_arn" {
  description = "启用了 accessManagement 时必填：list-enabled-baselines 中 IdentityCenterBaseline 的 enabledbaseline ARN。"
  type        = string
  default     = null
}

variable "controls" {
  description = "要在 NonProd OU 上启用的控制（Control Catalog ARN）。"
  type        = map(string)
  default = {
    # AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS：禁止为 root 用户创建访问密钥（预防性，SCP 实现）
    deny_root_access_keys = "arn:aws:controlcatalog:::control/8ui9y3oace2513xarz8aqojl7"
  }
}

data "aws_organizations_organization" "this" {}

resource "aws_organizations_organizational_unit" "workloads" {
  name      = "Workloads"
  parent_id = data.aws_organizations_organization.this.roots[0].id
}

resource "aws_organizations_organizational_unit" "nonprod" {
  name      = "NonProd"
  parent_id = aws_organizations_organizational_unit.workloads.id
}

# 注册 OU：部署 Config 记录器、审计角色等基线资源，并把 OU 纳入 Account Factory 的可选目标
resource "aws_controltower_baseline" "nonprod" {
  baseline_identifier = var.baseline_arn
  baseline_version    = var.baseline_version
  target_identifier   = aws_organizations_organizational_unit.nonprod.arn

  dynamic "parameters" {
    for_each = var.idc_baseline_arn == null ? [] : [var.idc_baseline_arn]
    content {
      key   = "IdentityCenterEnabledBaselineArn"
      value = parameters.value
    }
  }
}

resource "aws_controltower_control" "nonprod" {
  for_each           = var.controls
  control_identifier = each.value
  target_identifier  = aws_organizations_organizational_unit.nonprod.arn

  depends_on = [aws_controltower_baseline.nonprod]
}

output "nonprod_ou_arn" {
  value = aws_organizations_organizational_unit.nonprod.arn
}

output "enabled_baseline_arn" {
  value = aws_controltower_baseline.nonprod.arn
}
