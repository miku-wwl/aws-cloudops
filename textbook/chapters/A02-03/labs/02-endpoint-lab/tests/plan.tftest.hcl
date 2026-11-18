# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {
  override_during = plan

  mock_data "aws_availability_zones" {
    defaults = { names = ["us-east-1a"] }
  }
  mock_data "aws_caller_identity" {
    defaults = { account_id = "111122223333" }
  }
  mock_data "aws_iam_policy_document" {
    defaults = { json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}" }
  }
  mock_resource "aws_vpc_endpoint" {
    defaults = { prefix_list_id = "pl-63a5400a" }
  }
}

run "fault_state_by_default" {
  command = plan

  assert {
    condition     = length(aws_vpc_security_group_ingress_rule.endpoint_from_lambda) == 0
    error_message = "默认是故障态：终端节点 SG 没有 443 入站。"
  }
  assert {
    condition     = aws_vpc_endpoint.ssm.private_dns_enabled == true && aws_vpc.lab.enable_dns_hostnames && aws_vpc.lab.enable_dns_support
    error_message = "私有 DNS 需要终端节点开启 private_dns，且 VPC 两个 DNS 属性都为 true。"
  }
  assert {
    condition     = aws_vpc_endpoint.s3.vpc_endpoint_type == "Gateway" && aws_vpc_endpoint.ssm.vpc_endpoint_type == "Interface"
    error_message = "S3 用网关终端节点，SSM 用接口终端节点。"
  }
}

run "repair_adds_exactly_one_rule" {
  command = plan
  variables {
    allow_https = true
  }

  assert {
    condition     = length(aws_vpc_security_group_ingress_rule.endpoint_from_lambda) == 1 && aws_vpc_security_group_ingress_rule.endpoint_from_lambda[0].from_port == 443
    error_message = "修复只增加一条：443 来自 Lambda SG。"
  }
}

run "lambda_is_private_and_least_privilege" {
  command = plan

  assert {
    condition     = length(aws_lambda_function.probe.vpc_config) == 1 && aws_lambda_function.probe.runtime == "python3.14"
    error_message = "探针必须运行在 VPC 内（否则测的是公网路径）。"
  }
  assert {
    condition     = aws_lambda_function.probe.handler == "layers.handler"
    error_message = "与实验 5-1 共用同一份 layers.py。"
  }
}

run "endpoint_policy_is_optional" {
  command = plan
  variables {
    restrict_endpoint_policy = true
  }

  assert {
    condition     = strcontains(aws_vpc_endpoint.ssm.policy, "parameter/cloudops/a05/*")
    error_message = "终端节点策略只放行本实验参数路径。"
  }
}
