# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {
  override_during = plan

  mock_data "aws_availability_zones" {
    defaults = {
      names    = ["us-east-1a", "us-east-1b", "us-east-1c"]
      zone_ids = ["use1-az1", "use1-az2", "use1-az4"]
    }
  }
}

# 计算属性（资源 ID）在 plan 阶段未知：为两张 TGW 路由表给出不同的固定 ID，才能断言“关联自己、传播到对端”。
override_resource {
  target          = aws_ec2_transit_gateway_route_table.spoke["app"]
  override_during = plan
  values          = { id = "tgw-rtb-app" }
}

override_resource {
  target          = aws_ec2_transit_gateway_route_table.spoke["data"]
  override_during = plan
  values          = { id = "tgw-rtb-data" }
}

run "default_creates_nothing" {
  command = plan

  assert {
    condition     = length(aws_vpc.spoke) == 0 && length(aws_ec2_transit_gateway.hub) == 0 && length(aws_ec2_transit_gateway_vpc_attachment.spoke) == 0
    error_message = "enable_paid_lab = false 时不应创建任何资源。"
  }
}

run "tgw_does_not_use_default_table" {
  command = plan
  variables { enable_paid_lab = true }

  assert {
    condition = (
      aws_ec2_transit_gateway.hub[0].default_route_table_association == "disable" &&
      aws_ec2_transit_gateway.hub[0].default_route_table_propagation == "disable" &&
      alltrue([for a in aws_ec2_transit_gateway_vpc_attachment.spoke :
      !a.transit_gateway_default_route_table_association && !a.transit_gateway_default_route_table_propagation])
    )
    error_message = "TGW 与附件都必须关闭默认表的自动关联与自动传播，否则两张表的隔离会被默认表绕过。"
  }
}

run "each_attachment_spans_two_azs" {
  command = plan
  variables { enable_paid_lab = true }

  assert {
    condition = (
      aws_subnet.tgw["app-0"].cidr_block == "10.10.0.0/28" &&
      aws_subnet.tgw["app-1"].cidr_block == "10.10.0.16/28" &&
      aws_subnet.tgw["app-0"].availability_zone == "us-east-1a" &&
      aws_subnet.tgw["app-1"].availability_zone == "us-east-1b"
    )
    error_message = "每个 VPC 要在两个 AZ 各有一个 /28 附件子网。"
  }
}

run "associate_own_table_propagate_to_peer" {
  command = plan
  variables { enable_paid_lab = true }

  assert {
    condition = (
      aws_ec2_transit_gateway_route_table_association.spoke["app"].transit_gateway_route_table_id == aws_ec2_transit_gateway_route_table.spoke["app"].id &&
      aws_ec2_transit_gateway_route_table_propagation.cross["app"].transit_gateway_route_table_id == aws_ec2_transit_gateway_route_table.spoke["data"].id &&
      aws_ec2_transit_gateway_route_table_propagation.cross["data"].transit_gateway_route_table_id == aws_ec2_transit_gateway_route_table.spoke["app"].id
    )
    error_message = "附件关联自己的表，并把前缀传播进对端的表。"
  }

  assert {
    condition     = aws_route.to_peer["app"].destination_cidr_block == "10.20.0.0/16" && aws_route.to_peer["data"].destination_cidr_block == "10.10.0.0/16"
    error_message = "VPC 路由要把对端 CIDR 指向 TGW。"
  }
}

run "optional_blackhole" {
  command = plan
  variables {
    enable_paid_lab = true
    blackhole_cidr  = "10.20.5.0/24"
  }

  assert {
    condition     = length(aws_ec2_transit_gateway_route.blackhole) == 1 && aws_ec2_transit_gateway_route.blackhole[0].blackhole
    error_message = "设置 blackhole_cidr 后，app 表中应有一条黑洞路由。"
  }
}

run "bad_blackhole_rejected" {
  command = plan
  variables { blackhole_cidr = "10.20.5.0/33" }
  expect_failures = [var.blackhole_cidr]
}
