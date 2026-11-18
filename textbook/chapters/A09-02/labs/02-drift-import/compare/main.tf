# 第 16 讲实验 16-2 ②：代码声明与真实对象不一致时，plan 会怎样表达这份“漂移”（只读 plan，不 apply）
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
  type = string
}

import {
  to = aws_vpc.default
  id = var.vpc_id
}

resource "aws_vpc" "default" {
  cidr_block           = "172.31.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = false # 故意与真实值（true）不同：模拟“有人在控制台里打开了它”
}
