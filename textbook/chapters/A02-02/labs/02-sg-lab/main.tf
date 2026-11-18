###############################################################################
# 第 04 讲实验 4-2：安全组链（web → app → db）+ 客户托管前缀列表 + 可切换的 8080 规则
# 控制变量：client 与 server 放在同一个子网——同子网流量不经过 NACL，
# 所以“通 / 不通”只可能由安全组决定。默认不创建任何实例。
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
    tags = { Course = "cloudops-A02-02", ManagedBy = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "name" {
  type    = string
  default = "a04"
}

variable "allow_8080" {
  description = "实验开关：server SG 是否允许来自 client SG 的 TCP 8080。"
  type        = bool
  default     = false
}

variable "office_cidrs" {
  description = "办公网出口地址（写入客户托管前缀列表）。"
  type        = list(string)
  default     = ["203.0.113.0/24", "198.51.100.0/24"]
}

variable "prefix_list_max_entries" {
  description = "前缀列表容量。注意：引用它的每条 SG 规则按 max_entries 计入规则配额。"
  type        = number
  default     = 5
}

variable "enable_instances" {
  description = "创建 client / server 两台 t4g.nano 与 EIC 端点做真实验证（少量费用）。"
  type        = bool
  default     = false
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "lab" {
  cidr_block           = "10.40.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.name}-vpc" }
}

resource "aws_subnet" "app" {
  vpc_id            = aws_vpc.lab.id
  cidr_block        = "10.40.1.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]
  tags              = { Name = "${var.name}-app" }
}

# ---------------------------------------------------------------- 前缀列表
resource "aws_ec2_managed_prefix_list" "office" {
  name           = "${var.name}-office"
  address_family = "IPv4"
  max_entries    = var.prefix_list_max_entries

  dynamic "entry" {
    for_each = var.office_cidrs
    content {
      cidr        = entry.value
      description = "office egress"
    }
  }
}

data "aws_ec2_managed_prefix_list" "s3" {
  name = "com.amazonaws.${var.region}.s3"
}

# ---------------------------------------------------------------- 三层安全组链
resource "aws_security_group" "tier" {
  for_each    = toset(["web", "app", "db"])
  name        = "${var.name}-${each.key}"
  description = "${each.key} tier"
  vpc_id      = aws_vpc.lab.id
  tags        = { Name = "${var.name}-${each.key}" }
}

locals {
  sg = { for k, v in aws_security_group.tier : k => v.id }

  # 每条规则：所属 SG、方向、端口，以及来源 / 目的（sg、prefix list 或 cidr 三选一）
  tier_rules = {
    web_in_443_office = { sg = "web", dir = "in", port = 443, pl = aws_ec2_managed_prefix_list.office.id }
    web_out_8080_app  = { sg = "web", dir = "out", port = 8080, ref = "app" }
    app_in_8080_web   = { sg = "app", dir = "in", port = 8080, ref = "web" }
    app_out_5432_db   = { sg = "app", dir = "out", port = 5432, ref = "db" }
    app_out_443_s3    = { sg = "app", dir = "out", port = 443, pl = data.aws_ec2_managed_prefix_list.s3.id }
    db_in_5432_app    = { sg = "db", dir = "in", port = 5432, ref = "app" }
  }
}

resource "aws_vpc_security_group_ingress_rule" "tier" {
  for_each                     = { for k, r in local.tier_rules : k => r if r.dir == "in" }
  security_group_id            = local.sg[each.value.sg]
  ip_protocol                  = "tcp"
  from_port                    = each.value.port
  to_port                      = each.value.port
  referenced_security_group_id = try(local.sg[each.value.ref], null)
  prefix_list_id               = try(each.value.pl, null)
  description                  = each.key
}

resource "aws_vpc_security_group_egress_rule" "tier" {
  for_each                     = { for k, r in local.tier_rules : k => r if r.dir == "out" }
  security_group_id            = local.sg[each.value.sg]
  ip_protocol                  = "tcp"
  from_port                    = each.value.port
  to_port                      = each.value.port
  referenced_security_group_id = try(local.sg[each.value.ref], null)
  prefix_list_id               = try(each.value.pl, null)
  description                  = each.key
}

# ---------------------------------------------------------------- client / server 实验对
resource "aws_security_group" "client" {
  name        = "${var.name}-client"
  description = "test client"
  vpc_id      = aws_vpc.lab.id
}

resource "aws_security_group" "server" {
  name        = "${var.name}-server"
  description = "test server on 8080"
  vpc_id      = aws_vpc.lab.id
}

# client 出站只允许去 server 的 8080（Terraform 创建 SG 时会删除 AWS 默认的“全部出站”规则）
resource "aws_vpc_security_group_egress_rule" "client_to_server" {
  security_group_id            = aws_security_group.client.id
  referenced_security_group_id = aws_security_group.server.id
  ip_protocol                  = "tcp"
  from_port                    = 8080
  to_port                      = 8080
}

# 唯一的实验变量
resource "aws_vpc_security_group_ingress_rule" "server_8080" {
  count                        = var.allow_8080 ? 1 : 0
  security_group_id            = aws_security_group.server.id
  referenced_security_group_id = aws_security_group.client.id
  ip_protocol                  = "tcp"
  from_port                    = 8080
  to_port                      = 8080
  description                  = "lab switch: allow_8080"
}

output "security_groups" {
  value = merge(local.sg, { client = aws_security_group.client.id, server = aws_security_group.server.id })
}

output "office_prefix_list" {
  value = { id = aws_ec2_managed_prefix_list.office.id, max_entries = aws_ec2_managed_prefix_list.office.max_entries }
}
