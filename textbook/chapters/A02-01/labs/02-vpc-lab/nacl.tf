###############################################################################
# 私有子网的 NACL。规则全部用独立的 aws_network_acl_rule 管理，
# 不在 aws_network_acl 里写内联规则（两种写法混用会互相覆盖）。
###############################################################################
resource "aws_network_acl" "private" {
  vpc_id     = aws_vpc.lab.id
  subnet_ids = [aws_subnet.private.id]
  tags       = { Name = "${var.name}-acl-private" }
}

locals {
  # 每条规则：方向、编号、协议、CIDR、端口范围、动作
  open_rules = {
    "in-100-all"  = { egress = false, num = 100, proto = "-1", cidr = "0.0.0.0/0", from = 0, to = 0, action = "allow" }
    "out-100-all" = { egress = true, num = 100, proto = "-1", cidr = "0.0.0.0/0", from = 0, to = 0, action = "allow" }
  }

  strict_rules = merge(
    {
      # 入站：业务请求、经 EIC 进入的回包与访问 S3 等发起连接的回包（临时端口）
      "in-100-app"       = { egress = false, num = 100, proto = "tcp", cidr = var.public_cidr, from = 8080, to = 8080, action = "allow" }
      "in-120-ephemeral" = { egress = false, num = 120, proto = "tcp", cidr = "0.0.0.0/0", from = 1024, to = 65535, action = "allow" }
      # 出站：EIC 端点到公有子网实例的 SSH、访问 S3（HTTPS）
      "out-110-ssh"   = { egress = true, num = 110, proto = "tcp", cidr = var.public_cidr, from = 22, to = 22, action = "allow" }
      "out-120-https" = { egress = true, num = 120, proto = "tcp", cidr = "0.0.0.0/0", from = 443, to = 443, action = "allow" }
    },
    var.drop_ephemeral_out ? {} : {
      # 出站：给公有子网客户端的回包——目的端口是客户端的临时端口
      "out-100-ephemeral" = { egress = true, num = 100, proto = "tcp", cidr = var.public_cidr, from = 1024, to = 65535, action = "allow" }
    }
  )

  fault_rules = var.block_app_port ? {
    "in-090-deny-app" = { egress = false, num = 90, proto = "tcp", cidr = var.public_cidr, from = 8080, to = 8080, action = "deny" }
  } : {}

  nacl_rules = merge(var.nacl_mode == "open" ? local.open_rules : local.strict_rules, local.fault_rules)
}

resource "aws_network_acl_rule" "private" {
  for_each = local.nacl_rules

  network_acl_id = aws_network_acl.private.id
  egress         = each.value.egress
  rule_number    = each.value.num
  protocol       = each.value.proto
  rule_action    = each.value.action
  cidr_block     = each.value.cidr
  from_port      = each.value.from
  to_port        = each.value.to
}
