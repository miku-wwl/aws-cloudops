terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# Control Tower 的 Landing Zone API 在主区域（Home Region）调用。
provider "aws" {
  region = var.home_region

  default_tags {
    tags = {
      ManagedBy = "terraform"
      Course    = "cloudops-A00-01"
    }
  }
}
