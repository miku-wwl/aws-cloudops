###############################################################################
# 第 05 讲实验 5-3：没有 NAT 的私有子网，经 S3 网关终端节点与 SSM 接口终端节点访问 AWS API。
# 唯一的故障变量：接口终端节点安全组是否允许来自 Lambda SG 的 TCP 443（allow_https）。
# 费用提示：接口终端节点按“每个 AZ 每小时 + 处理流量”计费；本实验单 AZ、短时运行后立即 destroy。
###############################################################################
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.7"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = { Course = "cloudops-A02-03", ManagedBy = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "allow_https" {
  description = "故障开关：false = 终端节点 SG 没有 443 入站（故障态）；true = 只允许来自 Lambda SG 的 443。"
  type        = bool
  default     = false
}

variable "restrict_endpoint_policy" {
  description = "为 SSM 接口终端节点附加只允许读取 /cloudops/a05/* 的终端节点策略。"
  type        = bool
  default     = false
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "me" {}

# ---------------------------------------------------------------- 网络：只有 local 路由
resource "aws_vpc" "lab" {
  cidr_block           = "10.42.0.0/16"
  enable_dns_support   = true # Route 53 Resolver（VPC+2）可用
  enable_dns_hostnames = true # 私有 DNS 的前提之一
  tags                 = { Name = "a05-vpc" }
}

resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.lab.id
  cidr_block              = "10.42.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = false
  tags                    = { Name = "a05-private" }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.lab.id
  tags   = { Name = "a05-rt-private" }
}

resource "aws_route_table_association" "private" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private.id
}

# ---------------------------------------------------------------- 网关终端节点：路由层面
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.lab.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]
  tags              = { Name = "a05-s3-gateway" }
}

# ---------------------------------------------------------------- 安全组
resource "aws_security_group" "lambda" {
  name        = "a05-lambda"
  description = "probe function"
  vpc_id      = aws_vpc.lab.id
}

resource "aws_security_group" "endpoint" {
  name        = "a05-ssm-endpoint"
  description = "SSM interface endpoint ENI"
  vpc_id      = aws_vpc.lab.id
}

resource "aws_vpc_security_group_egress_rule" "lambda_to_endpoint" {
  security_group_id            = aws_security_group.lambda.id
  referenced_security_group_id = aws_security_group.endpoint.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}

resource "aws_vpc_security_group_egress_rule" "lambda_to_s3" {
  security_group_id = aws_security_group.lambda.id
  prefix_list_id    = aws_vpc_endpoint.s3.prefix_list_id
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

# 唯一的实验变量
resource "aws_vpc_security_group_ingress_rule" "endpoint_from_lambda" {
  count                        = var.allow_https ? 1 : 0
  security_group_id            = aws_security_group.endpoint.id
  referenced_security_group_id = aws_security_group.lambda.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}

# ---------------------------------------------------------------- 接口终端节点：DNS + ENI + SG
resource "aws_vpc_endpoint" "ssm" {
  vpc_id              = aws_vpc.lab.id
  service_name        = "com.amazonaws.${var.region}.ssm"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private.id]
  security_group_ids  = [aws_security_group.endpoint.id]
  private_dns_enabled = true
  policy = var.restrict_endpoint_policy ? jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = "*"
      Action    = ["ssm:GetParameter"]
      Resource  = "arn:aws:ssm:${var.region}:${data.aws_caller_identity.me.account_id}:parameter/cloudops/a05/*"
    }]
  }) : null
  tags = { Name = "a05-ssm-interface" }
}

# ---------------------------------------------------------------- 探针要读的两份数据
resource "aws_s3_bucket" "lab" {
  bucket_prefix = "a05-endpoint-lab-"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "lab" {
  bucket                  = aws_s3_bucket.lab.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_object" "hello" {
  bucket  = aws_s3_bucket.lab.id
  key     = "hello.txt"
  content = "A05-S3-GATEWAY-OK"
}

resource "aws_ssm_parameter" "hello" {
  name  = "/cloudops/a05/hello"
  type  = "String"
  value = "A05-SSM-INTERFACE-OK"
}
