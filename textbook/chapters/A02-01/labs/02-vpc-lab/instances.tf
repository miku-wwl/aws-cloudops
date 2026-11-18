###############################################################################
# 可选计算阶段（enable_instances = true）：两台没有公网 IP 的 t4g.nano，
# 通过 EC2 Instance Connect Endpoint（EIC，无小时费）登录，不开放任何来自互联网的 SSH。
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
  cidr_ipv4         = var.vpc_cidr
}

resource "aws_security_group" "client" {
  count       = var.enable_instances ? 1 : 0
  name        = "${var.name}-client"
  description = "client in public subnet"
  vpc_id      = aws_vpc.lab.id
}

resource "aws_security_group" "server" {
  count       = var.enable_instances ? 1 : 0
  name        = "${var.name}-server"
  description = "server in private subnet"
  vpc_id      = aws_vpc.lab.id
}

resource "aws_vpc_security_group_ingress_rule" "ssh_from_eic" {
  for_each                     = var.enable_instances ? { client = 0, server = 0 } : {}
  security_group_id            = each.key == "client" ? aws_security_group.client[0].id : aws_security_group.server[0].id
  referenced_security_group_id = aws_security_group.eic[0].id
  ip_protocol                  = "tcp"
  from_port                    = 22
  to_port                      = 22
}

resource "aws_vpc_security_group_ingress_rule" "app_from_client" {
  count                        = var.enable_instances ? 1 : 0
  security_group_id            = aws_security_group.server[0].id
  referenced_security_group_id = aws_security_group.client[0].id
  ip_protocol                  = "tcp"
  from_port                    = 8080
  to_port                      = 8080
}

resource "aws_vpc_security_group_egress_rule" "all_out" {
  for_each          = var.enable_instances ? { client = 0, server = 0 } : {}
  security_group_id = each.key == "client" ? aws_security_group.client[0].id : aws_security_group.server[0].id
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_ec2_instance_connect_endpoint" "eic" {
  count              = var.enable_instances ? 1 : 0
  subnet_id          = aws_subnet.private.id
  security_group_ids = [aws_security_group.eic[0].id]
  preserve_client_ip = false
  tags               = { Name = "${var.name}-eic" }
}

resource "aws_instance" "client" {
  count                       = var.enable_instances ? 1 : 0
  ami                         = data.aws_ssm_parameter.al2023[0].insecure_value
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.client[0].id]
  associate_public_ip_address = false
  metadata_options {
    http_tokens = "required" # 只允许 IMDSv2
  }
  tags = { Name = "${var.name}-client" }
}

resource "aws_instance" "server" {
  count                  = var.enable_instances ? 1 : 0
  ami                    = data.aws_ssm_parameter.al2023[0].insecure_value
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.private.id
  private_ip             = cidrhost(var.private_cidr, 20) # 10.20.2.20
  vpc_security_group_ids = [aws_security_group.server[0].id]
  user_data              = file("${path.module}/user_data/server.sh")
  metadata_options {
    http_tokens = "required"
  }
  tags = { Name = "${var.name}-server" }
}
