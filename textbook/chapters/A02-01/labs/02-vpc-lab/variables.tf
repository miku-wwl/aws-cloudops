variable "region" {
  type    = string
  default = "us-east-1"
}

variable "name" {
  description = "资源名前缀。"
  type        = string
  default     = "a02"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "public_cidr" {
  type    = string
  default = "10.20.1.0/24"
}

variable "private_cidr" {
  type    = string
  default = "10.20.2.0/24"
}

variable "nacl_mode" {
  description = "open：私有子网 NACL 全放行（只用 #90 演示 DENY）；strict：按最小需要放行，含临时端口规则。"
  type        = string
  default     = "open"

  validation {
    condition     = contains(["open", "strict"], var.nacl_mode)
    error_message = "nacl_mode 只能是 open 或 strict。"
  }
}

variable "block_app_port" {
  description = "故障 1：在私有子网 NACL 入站插入 #90 DENY TCP/8080（来自公有子网）。"
  type        = bool
  default     = false
}

variable "drop_ephemeral_out" {
  description = "故障 2（仅 strict 模式）：删掉出站临时端口规则，请求能进、回包出不去。"
  type        = bool
  default     = false
}

variable "enable_instances" {
  description = "创建两台 t4g.nano 与 EC2 Instance Connect Endpoint，用于真实 TCP/HTTP 验证（会产生少量费用）。"
  type        = bool
  default     = false
}

variable "instance_type" {
  type    = string
  default = "t4g.nano"
}

variable "enable_s3_gateway" {
  description = "为私有路由表添加 S3 网关终端节点（无小时费）。"
  type        = bool
  default     = false
}
