# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {
  override_during = plan

  mock_data "aws_caller_identity" {
    defaults = { account_id = "111122223333" }
  }

  mock_data "aws_ssm_parameter" {
    defaults = { insecure_value = "ami-0123456789abcdef0" }
  }

  mock_data "aws_ec2_instance_type_offerings" {
    defaults = { locations = ["us-east-1b", "us-east-1a"] }
  }

  mock_resource "aws_iam_role" {
    defaults = { arn = "arn:aws:iam::111122223333:role/a10-lab01-automation" }
  }
}

run "default_mode_creates_no_compute" {
  command = plan

  assert {
    condition     = length(aws_instance.lab) == 0 && length(aws_vpc.lab) == 0 && length(aws_vpc_security_group_egress_rule.https) == 0
    error_message = "默认模式不得创建 VPC 或 EC2。"
  }
}

run "command_document_cannot_be_injected" {
  command = plan

  assert {
    condition = (
      !contains(keys(jsondecode(aws_ssm_document.diagnostics.content)), "parameters") &&
      jsondecode(aws_ssm_document.diagnostics.content).mainSteps[0].precondition.StringEquals == ["platformType", "Linux"]
    )
    error_message = "诊断文档不应有参数（调用者无法注入命令），并且只在 Linux 上运行。"
  }
}

run "runbook_uses_its_own_read_only_role" {
  command = plan

  assert {
    condition = (
      jsondecode(aws_ssm_document.inventory.content).assumeRole == aws_iam_role.automation.arn &&
      [for s in jsondecode(aws_ssm_document.inventory.content).mainSteps : s.inputs.Api] == ["DescribeInstances", "DescribeInstanceInformation"]
    )
    error_message = "Runbook 用专门的执行角色，只调用两个只读 API。"
  }

  assert {
    condition     = jsondecode(aws_iam_role.automation.assume_role_policy).Statement[0].Condition.StringEquals["aws:SourceAccount"] == "111122223333"
    error_message = "执行角色的信任策略要有 aws:SourceAccount 条件（防混淆代理）。"
  }
}

run "instance_mode_is_hardened" {
  command = plan
  variables {
    create_lab_instance = true
  }

  assert {
    condition = (
      one(aws_instance.lab[0].metadata_options).http_tokens == "required" &&
      one(aws_instance.lab[0].root_block_device).encrypted == true &&
      aws_instance.lab[0].iam_instance_profile == "a10-lab01-node" &&
      aws_instance.lab[0].ami == "ami-0123456789abcdef0"
    )
    error_message = "实例：IMDSv2、加密根卷、挂实例配置文件、AMI 来自公共参数。"
  }

  assert {
    condition     = aws_iam_role_policy_attachment.core[0].policy_arn == "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    error_message = "节点角色挂 AmazonSSMManagedInstanceCore。"
  }

  assert {
    condition = (
      length(aws_vpc_security_group_egress_rule.https) == 1 &&
      aws_vpc_security_group_egress_rule.https[0].from_port == 443 &&
      aws_vpc_security_group_egress_rule.https[0].ip_protocol == "tcp"
    )
    error_message = "唯一的出站规则是 TCP 443。"
  }

  assert {
    condition     = aws_subnet.public[0].availability_zone == "us-east-1a"
    error_message = "子网放在提供该机型的可用区（排序后的第一个）。"
  }
}

run "fault_switch_removes_the_only_egress" {
  command = plan
  variables {
    create_lab_instance = true
    allow_ssm_egress    = false
  }

  assert {
    condition     = length(aws_vpc_security_group_egress_rule.https) == 0 && length(aws_instance.lab) == 1
    error_message = "故障开关只删除出站规则，实例保留。"
  }
}

run "x86_instance_type_is_rejected" {
  command = plan
  variables {
    instance_type = "t3.micro"
  }
  expect_failures = [var.instance_type]
}
