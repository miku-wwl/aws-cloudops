###############################################################################
# 第 14 讲实验 14-2：一个可以“故障注入 → 取证 → 最小恢复”的 Web 入口
#   VPC 10.80.0.0/16、公有子网、IGW、默认路由
#   安全组：只放行操作者当前公网 IPv4 /32 的 TCP 80（独立的规则资源，便于精确检测漂移）；
#           出站只开 443（安装 nginx 用），不开 SSH
#   EC2：t4g.nano（AL2023 arm64）+ nginx，强制 IMDSv2、加密 gp3
# 费用：约 0.01 美元/小时（实例 + 公网 IPv4 + 根卷），做完立即 destroy。
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
    tags = { Course = "cloudops-A08-01", Chapter = "A08-01", ManagedBy = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "client_cidr" {
  description = "操作者当前的公网 IPv4，必须是 /32（例如 curl -s https://checkip.amazonaws.com 的结果加 /32）。"
  type        = string
  validation {
    condition     = can(cidrhost(var.client_cidr, 0)) && endswith(var.client_cidr, "/32") && var.client_cidr != "0.0.0.0/32"
    error_message = "client_cidr 必须是单个公网 IPv4 的 /32。"
  }
}

data "aws_ssm_parameter" "al2023_arm64" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

data "aws_ec2_instance_type_offerings" "here" {
  location_type = "availability-zone"
  filter {
    name   = "instance-type"
    values = ["t4g.nano"]
  }
}

resource "aws_vpc" "lab" {
  cidr_block           = "10.80.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "a14-vpc" }
}

resource "aws_internet_gateway" "lab" {
  vpc_id = aws_vpc.lab.id
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.lab.id
  cidr_block              = "10.80.1.0/24"
  availability_zone       = sort(data.aws_ec2_instance_type_offerings.here.locations)[0]
  map_public_ip_on_launch = true
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.lab.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.lab.id
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "web" {
  name_prefix = "a14-web-"
  description = "A14 lab web entry - operator /32 only"
  vpc_id      = aws_vpc.lab.id
  # 不写内联规则：入站、出站各用独立资源管理，不能与内联规则或 aws_security_group_rule 混用
}

resource "aws_vpc_security_group_ingress_rule" "http_from_operator" {
  security_group_id = aws_security_group.web.id
  description       = "HTTP from the operator only"
  cidr_ipv4         = var.client_cidr
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_egress_rule" "https" {
  security_group_id = aws_security_group.web.id
  description       = "package repositories over HTTPS"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_instance" "web" {
  ami                    = data.aws_ssm_parameter.al2023_arm64.insecure_value
  instance_type          = "t4g.nano"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]
  user_data              = <<-EOT
    #!/bin/bash
    dnf install -y nginx
    echo "a14 ok $(hostname)" > /usr/share/nginx/html/index.html
    systemctl enable --now nginx
  EOT

  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 8
    encrypted   = true
    tags        = { Name = "a14-root", Chapter = "A08-01" }
  }

  tags = { Name = "a14-web" }
}

output "test_url" {
  value = "http://${aws_instance.web.public_ip}/"
}

output "security_group_id" {
  value = aws_security_group.web.id
}

output "ingress_rule_id" {
  value = aws_vpc_security_group_ingress_rule.http_from_operator.security_group_rule_id
}

output "instance_id" {
  value = aws_instance.web.id
}
