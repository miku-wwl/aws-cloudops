# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {
  override_during = plan

  mock_data "aws_ssm_parameter" {
    defaults = { insecure_value = "ami-0123456789abcdef0" }
  }

  mock_data "aws_ec2_instance_type_offerings" {
    defaults = { locations = ["us-east-1b", "us-east-1a"] }
  }
}

variables {
  client_cidr = "203.0.113.10/32"
}

run "only_the_operator_can_reach_port_80" {
  command = plan

  assert {
    condition = (
      aws_vpc_security_group_ingress_rule.http_from_operator.cidr_ipv4 == "203.0.113.10/32" &&
      aws_vpc_security_group_ingress_rule.http_from_operator.from_port == 80 &&
      aws_vpc_security_group_ingress_rule.http_from_operator.to_port == 80
    )
    error_message = "入站只放行操作者 /32 的 TCP 80。"
  }

  assert {
    condition     = aws_vpc_security_group_egress_rule.https.from_port == 443 && aws_vpc_security_group_egress_rule.https.to_port == 443
    error_message = "出站只开 443。"
  }
}

run "instance_is_hardened_and_serves_http" {
  command = plan

  assert {
    condition = (
      one(aws_instance.web.metadata_options).http_tokens == "required" &&
      one(aws_instance.web.root_block_device).encrypted &&
      strcontains(aws_instance.web.user_data, "nginx")
    )
    error_message = "IMDSv2、加密根卷、安装 nginx。"
  }
}

run "world_open_cidr_is_rejected" {
  command = plan
  variables {
    client_cidr = "0.0.0.0/0"
  }
  expect_failures = [var.client_cidr]
}

run "subnet_range_is_rejected" {
  command = plan
  variables {
    client_cidr = "203.0.113.0/24"
  }
  expect_failures = [var.client_cidr]
}
