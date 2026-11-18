###############################################################################
# 可选：两台无公网 IP 的实例 + EC2 Instance Connect Endpoint（与第 03 讲相同的登录方式）
###############################################################################
data "aws_ssm_parameter" "al2023" {
  count = var.enable_instances ? 1 : 0
  name  = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

resource "aws_security_group" "eic" {
  count       = var.enable_instances ? 1 : 0
  name        = "${var.name}-eic"
  description = "EC2 Instance Connect Endpoint"
  vpc_id      = aws_vpc.lab.id
}

resource "aws_vpc_security_group_egress_rule" "eic_ssh" {
  count             = var.enable_instances ? 1 : 0
  security_group_id = aws_security_group.eic[0].id
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
  cidr_ipv4         = aws_vpc.lab.cidr_block
}

resource "aws_vpc_security_group_ingress_rule" "ssh_from_eic" {
  for_each                     = var.enable_instances ? { client = aws_security_group.client.id, server = aws_security_group.server.id } : {}
  security_group_id            = each.value
  referenced_security_group_id = aws_security_group.eic[0].id
  ip_protocol                  = "tcp"
  from_port                    = 22
  to_port                      = 22
}

resource "aws_ec2_instance_connect_endpoint" "eic" {
  count              = var.enable_instances ? 1 : 0
  subnet_id          = aws_subnet.app.id
  security_group_ids = [aws_security_group.eic[0].id]
}

resource "aws_instance" "lab" {
  for_each               = var.enable_instances ? { client = 10, server = 20 } : {}
  ami                    = data.aws_ssm_parameter.al2023[0].insecure_value
  instance_type          = "t4g.nano"
  subnet_id              = aws_subnet.app.id
  private_ip             = cidrhost(aws_subnet.app.cidr_block, each.value)
  vpc_security_group_ids = [each.key == "client" ? aws_security_group.client.id : aws_security_group.server.id]
  user_data = each.key == "server" ? join("\n", [
    "#!/bin/bash",
    "mkdir -p /opt/a04 && echo ok > /opt/a04/health",
    "nohup python3 -m http.server 8080 --bind 0.0.0.0 --directory /opt/a04 >/var/log/a04-http.log 2>&1 &",
  ]) : null
  metadata_options {
    http_tokens = "required"
  }
  tags = { Name = "${var.name}-${each.key}" }
}
