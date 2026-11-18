###############################################################################
# 第 17 讲实验 17-2：两个 Spoke VPC + 一个 TGW + 两张 TGW 路由表（交叉传播）
#
#   enable_paid_lab = false（默认）：plan 中 0 个资源，只读取一次可用区列表。
#   enable_paid_lab = true：2 个 VPC、每个 VPC 两个 AZ 的 /28 附件子网、TGW（关闭默认关联与默认传播）、
#     每个附件关联“自己的”TGW 路由表、把自己的前缀传播进“对端的”表、VPC 路由指向 TGW。
#   blackhole_cidr（可选）：在 app 的 TGW 表里加一条更精确的黑洞，演示最长前缀匹配。
#
# 费用（us-east-1，Price List API，2026-11-18）：VPC 附件 0.05 美元/小时 × 2 = 0.10 美元/小时；
#   TGW 本身不按小时收费；数据处理 0.02 美元/GB（本实验不产生流量）。
#   不创建 EC2、VPN、Direct Connect、Resolver 端点。做完立即 destroy，并核对附件已删除。
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
    tags = { Course = "cloudops-A10-01", Chapter = "A10-01", ManagedBy = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "enable_paid_lab" {
  description = "true 才创建任何资源（会按附件小时计费）。"
  type        = bool
  default     = false
}

variable "name" {
  type    = string
  default = "a17"
}

variable "blackhole_cidr" {
  description = "可选：在 app 的 TGW 路由表中加一条黑洞路由，例如 10.20.5.0/24。"
  type        = string
  default     = ""
  validation {
    condition     = var.blackhole_cidr == "" || can(cidrhost(var.blackhole_cidr, 0))
    error_message = "blackhole_cidr 必须为空或合法的 CIDR。"
  }
}

data "aws_availability_zones" "az" {
  state = "available"
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

locals {
  vpcs    = { app = { cidr = "10.10.0.0/16" }, data = { cidr = "10.20.0.0/16" } }
  peer    = { app = "data", data = "app" }
  subnets = { for p in setproduct(keys(local.vpcs), [0, 1]) : "${p[0]}-${p[1]}" => { vpc = p[0], idx = p[1] } }

  spokes        = var.enable_paid_lab ? local.vpcs : {}
  spoke_subnets = var.enable_paid_lab ? local.subnets : {}
}

resource "aws_vpc" "spoke" {
  for_each             = local.spokes
  cidr_block           = each.value.cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.name}-${each.key}" }
}

# 每个 AZ 一个 /28 专用附件子网：TGW 在其中放一个网卡；没有附件子网的 AZ 进不了 TGW
resource "aws_subnet" "tgw" {
  for_each          = local.spoke_subnets
  vpc_id            = aws_vpc.spoke[each.value.vpc].id
  cidr_block        = cidrsubnet(local.vpcs[each.value.vpc].cidr, 12, each.value.idx)
  availability_zone = data.aws_availability_zones.az.names[each.value.idx]
  tags              = { Name = "${var.name}-${each.key}-tgw" }
}

resource "aws_route_table" "spoke" {
  for_each = local.spokes
  vpc_id   = aws_vpc.spoke[each.key].id
  tags     = { Name = "${var.name}-${each.key}-rt" }
}

resource "aws_route_table_association" "tgw" {
  for_each       = local.spoke_subnets
  subnet_id      = aws_subnet.tgw[each.key].id
  route_table_id = aws_route_table.spoke[each.value.vpc].id
}

resource "aws_ec2_transit_gateway" "hub" {
  count                           = var.enable_paid_lab ? 1 : 0
  description                     = "${var.name} hub (lab)"
  default_route_table_association = "disable" # 不让新附件自动关联到默认表
  default_route_table_propagation = "disable" # 不让新附件自动把前缀传播到默认表
  auto_accept_shared_attachments  = "disable"
  dns_support                     = "enable"
  tags                            = { Name = "${var.name}-hub" }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "spoke" {
  for_each           = local.spokes
  transit_gateway_id = aws_ec2_transit_gateway.hub[0].id
  vpc_id             = aws_vpc.spoke[each.key].id
  subnet_ids         = [for k, s in local.subnets : aws_subnet.tgw[k].id if s.vpc == each.key]

  transit_gateway_default_route_table_association = false
  transit_gateway_default_route_table_propagation = false
  tags                                            = { Name = "${var.name}-${each.key}-att" }
}

resource "aws_ec2_transit_gateway_route_table" "spoke" {
  for_each           = local.spokes
  transit_gateway_id = aws_ec2_transit_gateway.hub[0].id
  tags               = { Name = "${var.name}-${each.key}-tgw-rt" }
}

# 关联：从这个附件进入 TGW 的流量查哪张表（一个附件只能关联一张）
resource "aws_ec2_transit_gateway_route_table_association" "spoke" {
  for_each                       = local.spokes
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.spoke[each.key].id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.spoke[each.key].id
}

# 传播：把自己的 VPC CIDR 装进“对端查的那张表”（一个附件可以传播到多张）
resource "aws_ec2_transit_gateway_route_table_propagation" "cross" {
  for_each                       = local.spokes
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.spoke[each.key].id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.spoke[local.peer[each.key]].id
}

# VPC 子网路由不会自动生成：要自己把对端 CIDR 指向 TGW
resource "aws_route" "to_peer" {
  for_each               = local.spokes
  route_table_id         = aws_route_table.spoke[each.key].id
  destination_cidr_block = local.vpcs[local.peer[each.key]].cidr
  transit_gateway_id     = aws_ec2_transit_gateway.hub[0].id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.spoke]
}

resource "aws_ec2_transit_gateway_route" "blackhole" {
  count                          = var.enable_paid_lab && var.blackhole_cidr != "" ? 1 : 0
  destination_cidr_block         = var.blackhole_cidr
  blackhole                      = true
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.spoke["app"].id
}

output "estimated_usd_per_hour" {
  description = "附件小时费（不含数据处理）。"
  value       = var.enable_paid_lab ? 2 * 0.05 : 0
}

output "verify" {
  value = var.enable_paid_lab ? join("\n", [
    "aws ec2 describe-transit-gateway-attachments --filters Name=transit-gateway-id,Values=${aws_ec2_transit_gateway.hub[0].id}",
    "aws ec2 search-transit-gateway-routes --transit-gateway-route-table-id ${aws_ec2_transit_gateway_route_table.spoke["app"].id} --filters Name=type,Values=static,propagated",
  ]) : "enable_paid_lab = false：没有创建任何资源"
}
