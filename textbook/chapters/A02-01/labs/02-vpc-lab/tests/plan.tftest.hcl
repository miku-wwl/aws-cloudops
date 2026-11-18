# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = {
      names = ["us-east-1a", "us-east-1b"]
    }
  }
  mock_data "aws_ssm_parameter" {
    defaults = {
      insecure_value = "ami-0123456789abcdef0"
    }
  }
}

run "baseline_has_no_compute_and_no_private_default_route" {
  command = plan

  assert {
    condition     = length(aws_instance.server) == 0 && length(aws_ec2_instance_connect_endpoint.eic) == 0
    error_message = "默认不应创建任何计算资源。"
  }
  assert {
    condition     = aws_route.public_default.destination_cidr_block == "0.0.0.0/0"
    error_message = "公有路由表应有指向 IGW 的默认路由。"
  }
  assert {
    condition     = length(aws_vpc_endpoint.s3) == 0
    error_message = "默认不创建 S3 网关终端节点。"
  }
  assert {
    condition     = aws_subnet.public.map_public_ip_on_launch == false
    error_message = "公有子网也不应自动分配公网 IP。"
  }
}

run "fault_rule_90_is_evaluated_first" {
  command = plan
  variables {
    block_app_port = true
  }

  assert {
    condition = (
      aws_network_acl_rule.private["in-090-deny-app"].rule_number == 90 &&
      aws_network_acl_rule.private["in-090-deny-app"].rule_action == "deny" &&
      aws_network_acl_rule.private["in-090-deny-app"].from_port == 8080
    )
    error_message = "应插入编号 90 的 DENY TCP/8080。"
  }
  assert {
    condition     = aws_network_acl_rule.private["in-090-deny-app"].rule_number < aws_network_acl_rule.private["in-100-all"].rule_number
    error_message = "DENY 的编号必须小于 ALLOW，才会先被评估。"
  }
}

run "strict_mode_allows_ephemeral_responses" {
  command = plan
  variables {
    nacl_mode = "strict"
  }

  assert {
    condition = (
      aws_network_acl_rule.private["out-100-ephemeral"].egress == true &&
      aws_network_acl_rule.private["out-100-ephemeral"].from_port == 1024 &&
      aws_network_acl_rule.private["out-100-ephemeral"].to_port == 65535
    )
    error_message = "严格模式必须放行发往客户端临时端口的出站回包。"
  }
}

run "drop_ephemeral_out_removes_return_path" {
  command = plan
  variables {
    nacl_mode          = "strict"
    drop_ephemeral_out = true
  }

  assert {
    condition     = !contains(keys(aws_network_acl_rule.private), "out-100-ephemeral")
    error_message = "故障 2 应删除出站临时端口规则。"
  }
}

run "instances_are_private_and_imdsv2_only" {
  command = plan
  variables {
    enable_instances = true
  }

  assert {
    condition     = aws_instance.client[0].associate_public_ip_address == false
    error_message = "客户端不需要公网 IP：通过 EIC 登录。"
  }
  assert {
    condition     = aws_instance.server[0].metadata_options[0].http_tokens == "required"
    error_message = "实例应只允许 IMDSv2。"
  }
  assert {
    condition     = aws_instance.server[0].private_ip == "10.20.2.20"
    error_message = "服务器固定为 10.20.2.20，便于和例题对照。"
  }
}

run "reject_unknown_nacl_mode" {
  command = plan
  variables {
    nacl_mode = "paranoid"
  }
  expect_failures = [var.nacl_mode]
}
