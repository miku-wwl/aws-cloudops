# 第 16 讲实验 16-2 ①：用 import 块 + -generate-config-out，从“真实对象”反推出 HCL（只读 plan，不导入）
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
  region = "us-east-1"
}

variable "vpc_id" {
  type        = string
  description = "账户中默认 VPC 的 ID（aws ec2 describe-vpcs --filters Name=isDefault,Values=true）"
}

import {
  to = aws_vpc.default
  id = var.vpc_id
}
