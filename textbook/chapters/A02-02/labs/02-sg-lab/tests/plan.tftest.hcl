# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {
  # 让 mock 生成的“计算属性”（如前缀列表 ID）在 plan 阶段就可用
  override_during = plan

  mock_resource "aws_ec2_managed_prefix_list" {
    defaults = { id = "pl-0office00000000001" }
  }
  mock_resource "aws_subnet" {
    defaults = { id = "subnet-0app00000000001" }
  }
  mock_data "aws_availability_zones" {
    defaults = { names = ["us-east-1a"] }
  }
  mock_data "aws_ec2_managed_prefix_list" {
    defaults = { id = "pl-63a5400a" }
  }
  mock_data "aws_ssm_parameter" {
    defaults = { insecure_value = "ami-0123456789abcdef0" }
  }
}

run "no_rule_is_open_to_the_world" {
  command = plan

  assert {
    condition = alltrue([
      for r in aws_vpc_security_group_ingress_rule.tier : r.cidr_ipv4 == null
    ])
    error_message = "三层链中不应出现基于 CIDR 的入站规则，更不能有 0.0.0.0/0。"
  }
  assert {
    condition     = aws_vpc_security_group_ingress_rule.tier["web_in_443_office"].prefix_list_id != null
    error_message = "web 层只接受来自办公网前缀列表的 443。"
  }
}

run "db_only_reachable_from_app" {
  command = plan

  assert {
    condition = (
      aws_vpc_security_group_ingress_rule.tier["db_in_5432_app"].from_port == 5432 &&
      length([for k, r in aws_vpc_security_group_ingress_rule.tier : k if startswith(k, "db_")]) == 1
    )
    error_message = "db 层只能有一条入站规则：5432 来自 app SG。"
  }
  assert {
    condition     = length([for k, r in aws_vpc_security_group_egress_rule.tier : k if startswith(k, "db_")]) == 0
    error_message = "db 层不需要任何出站规则（回包由连接跟踪放行）。"
  }
}

run "lab_switch_off_means_no_8080" {
  command = plan

  assert {
    condition     = length(aws_vpc_security_group_ingress_rule.server_8080) == 0
    error_message = "默认不放行 8080：先观察失败。"
  }
}

run "lab_switch_on_adds_exactly_one_rule" {
  command = plan
  variables {
    allow_8080 = true
  }

  assert {
    condition     = length(aws_vpc_security_group_ingress_rule.server_8080) == 1
    error_message = "allow_8080 = true 只应增加一条入站规则。"
  }
}

run "prefix_list_weight" {
  command = plan

  assert {
    condition     = aws_ec2_managed_prefix_list.office.max_entries == 5 && length(aws_ec2_managed_prefix_list.office.entry) == 2
    error_message = "前缀列表容量 5、当前 2 条；引用它的规则按 5 条计入配额。"
  }
}

run "instances_share_one_subnet" {
  command = plan
  variables {
    enable_instances = true
  }

  assert {
    condition     = aws_instance.lab["client"].subnet_id == aws_instance.lab["server"].subnet_id
    error_message = "控制变量：两台实例必须在同一子网，NACL 不参与。"
  }
}
