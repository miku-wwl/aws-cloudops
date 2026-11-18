###############################################################################
# 第 10 讲实验 10-3：没有 SSH 的受控运维
#   默认模式（零费用）：一个 Command 文档（固定的只读诊断命令，无参数）+ 一个 Automation Runbook
#                      （只调用 DescribeInstances / DescribeInstanceInformation）+ Runbook 的执行角色
#   实例模式（create_lab_instance = true，按小时计费）：VPC、公有子网、IGW、无入站的安全组、
#                      可开关的出站 443、带 AmazonSSMManagedInstanceCore 的实例配置文件、
#                      1 台 t4g.nano（AL2023 arm64，强制 IMDSv2，加密 gp3）
# 故障开关：allow_ssm_egress = false 删除唯一的出站规则（之后要重启实例，见教材）。
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
    tags = { Course = "cloudops-A05-01", Chapter = "A05-01", ManagedBy = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "suffix" {
  type    = string
  default = "lab01"
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{2,19}$", var.suffix))
    error_message = "suffix 只能包含小写字母、数字和连字符，长度 3–20。"
  }
}

variable "create_lab_instance" {
  description = "true 才创建 VPC 与 EC2（产生费用）；默认只建文档与角色。"
  type        = bool
  default     = false
}

variable "allow_ssm_egress" {
  description = "故障注入开关：false 时删除安全组唯一的出站 443 规则。"
  type        = bool
  default     = true
}

variable "instance_type" {
  description = "必须是 Graviton（arm64）机型，与 AMI 架构一致。"
  type        = string
  default     = "t4g.nano"
  validation {
    condition     = can(regex("^[a-z]+[0-9]+g[a-z]*\\.[a-z0-9]+$", var.instance_type))
    error_message = "请选择 Graviton 机型（如 t4g.nano、t4g.micro），AMI 是 arm64。"
  }
}

data "aws_caller_identity" "current" {}

locals {
  name = "a10-${var.suffix}"
  lab  = var.create_lab_instance ? 1 : 0
}

# ============================================================================ 默认模式：文档 + Runbook 角色
resource "aws_ssm_document" "diagnostics" {
  name            = "${local.name}-diagnostics"
  document_type   = "Command"
  document_format = "JSON"
  content = jsonencode({
    schemaVersion = "2.2"
    description   = "Read-only diagnostics: disk, load, OS release, agent version. No parameters, so callers cannot inject commands."
    mainSteps = [{
      action       = "aws:runShellScript"
      name         = "ReadOnlyDiagnostics"
      precondition = { StringEquals = ["platformType", "Linux"] }
      inputs = {
        timeoutSeconds = "60"
        runCommand = [
          "echo '== disk'; df -h /",
          "echo '== load'; uptime",
          "echo '== os'; grep -E '^(NAME|VERSION)=' /etc/os-release",
          "echo '== agent'; rpm -q amazon-ssm-agent || true",
        ]
      }
    }]
  })
}

resource "aws_iam_role" "automation" {
  name = "${local.name}-automation"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ssm.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = { # 防“混淆代理”：只接受本账户的 Automation 执行来承担
        StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
        ArnLike      = { "aws:SourceArn" = "arn:aws:ssm:*:${data.aws_caller_identity.current.account_id}:automation-execution/*" }
      }
    }]
  })
}

resource "aws_iam_role_policy" "automation_read" {
  name = "read-only-inventory"
  role = aws_iam_role.automation.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ec2:DescribeInstances", "ssm:DescribeInstanceInformation"]
      Resource = "*"
    }]
  })
}

resource "aws_ssm_document" "inventory" {
  name            = "${local.name}-inventory"
  document_type   = "Automation"
  document_format = "JSON"
  content = jsonencode({
    schemaVersion = "0.3"
    description   = "Read-only inventory of one instance through the control plane (works even when the agent is offline)."
    assumeRole    = aws_iam_role.automation.arn
    parameters = {
      InstanceId = { type = "String", allowedPattern = "^i-[0-9a-f]{8,17}$" }
    }
    mainSteps = [
      {
        name    = "DescribeInstance"
        action  = "aws:executeAwsApi"
        inputs  = { Service = "ec2", Api = "DescribeInstances", InstanceIds = ["{{ InstanceId }}"] }
        outputs = [{ Name = "State", Selector = "$.Reservations[0].Instances[0].State.Name", Type = "String" }]
      },
      {
        name   = "DescribeNode"
        action = "aws:executeAwsApi"
        inputs = {
          Service = "ssm", Api = "DescribeInstanceInformation"
          Filters = [{ Key = "InstanceIds", Values = ["{{ InstanceId }}"] }]
        }
        outputs = [{ Name = "Nodes", Selector = "$.InstanceInformationList", Type = "MapList" }]
      },
    ]
    outputs = ["DescribeInstance.State", "DescribeNode.Nodes"]
  })
}

# ============================================================================ 实例模式（有费用）
data "aws_ssm_parameter" "al2023_arm64" {
  count = local.lab
  name  = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

data "aws_ec2_instance_type_offerings" "here" {
  count         = local.lab
  location_type = "availability-zone"
  filter {
    name   = "instance-type"
    values = [var.instance_type]
  }
}

resource "aws_vpc" "lab" {
  count                = local.lab
  cidr_block           = "10.57.0.0/16"
  enable_dns_support   = true # Agent 要解析 ssm.<region>.amazonaws.com
  enable_dns_hostnames = true
  tags                 = { Name = "${local.name}-vpc" }
}

resource "aws_internet_gateway" "lab" {
  count  = local.lab
  vpc_id = aws_vpc.lab[0].id
}

resource "aws_subnet" "public" {
  count                   = local.lab
  vpc_id                  = aws_vpc.lab[0].id
  cidr_block              = "10.57.1.0/24"
  availability_zone       = sort(data.aws_ec2_instance_type_offerings.here[0].locations)[0]
  map_public_ip_on_launch = true # 公网 IPv4 按小时计费；生产应改为私有子网 + 接口端点
}

resource "aws_route_table" "public" {
  count  = local.lab
  vpc_id = aws_vpc.lab[0].id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.lab[0].id
  }
}

resource "aws_route_table_association" "public" {
  count          = local.lab
  subnet_id      = aws_subnet.public[0].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_security_group" "node" {
  count       = local.lab
  name_prefix = "${local.name}-node-"
  description = "A10 lab node - no inbound rules at all"
  vpc_id      = aws_vpc.lab[0].id
  # 不写任何内联规则：Terraform 会删掉 AWS 默认的“全部出站”，出站只剩下面这一条（可开关）
}

resource "aws_vpc_security_group_egress_rule" "https" {
  count             = var.create_lab_instance && var.allow_ssm_egress ? 1 : 0
  security_group_id = aws_security_group.node[0].id
  description       = "SSM endpoints over HTTPS"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_iam_role" "node" {
  count = local.lab
  name  = "${local.name}-node"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy_attachment" "core" {
  count      = local.lab
  role       = aws_iam_role.node[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "node" {
  count = local.lab
  name  = "${local.name}-node"
  role  = aws_iam_role.node[0].name
}

resource "aws_instance" "lab" {
  count                  = local.lab
  ami                    = data.aws_ssm_parameter.al2023_arm64[0].insecure_value
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.node[0].id]
  iam_instance_profile   = aws_iam_instance_profile.node[0].name

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # 强制 IMDSv2
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 8
    encrypted             = true
    delete_on_termination = true
    tags                  = { Name = "${local.name}-root", Chapter = "A05-01" } # default_tags 不会自动打到根卷上
  }

  tags = { Name = "${local.name}-node", Env = "lab" } # Env=lab 与实验 10-2 的操作者策略对应
}

# ============================================================================ 输出
output "command_document" {
  value = aws_ssm_document.diagnostics.name
}

output "automation_document" {
  value = aws_ssm_document.inventory.name
}

output "automation_role_arn" {
  value = aws_iam_role.automation.arn
}

output "instance_id" {
  value = one(aws_instance.lab[*].id)
}

output "security_group_id" {
  value = one(aws_security_group.node[*].id)
}
