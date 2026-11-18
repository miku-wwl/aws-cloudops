output "vpc_id" {
  value = aws_vpc.lab.id
}

output "private_rt_id" {
  value = aws_route_table.private.id
}

output "private_nacl_id" {
  value = aws_network_acl.private.id
}

output "private_nacl_rules" {
  description = "便于评审：生效的私有子网 NACL 规则（方向/编号/协议/端口/动作）。"
  value       = { for k, r in local.nacl_rules : k => "${r.egress ? "OUT" : "IN"} #${r.num} ${r.action} ${r.proto} ${r.from}-${r.to} ${r.cidr}" }
}

output "client_instance_id" {
  value = try(aws_instance.client[0].id, null)
}

output "server_private_ip" {
  value = try(aws_instance.server[0].private_ip, null)
}
