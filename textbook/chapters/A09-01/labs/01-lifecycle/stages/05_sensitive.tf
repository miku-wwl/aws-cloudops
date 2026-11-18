# 阶段 5：sensitive 只是“不在终端显示”，不是“不写进计划文件”
variable "db_password" {
  type      = string
  sensitive = true
  default   = "Example-Not-A-Real-Secret-42"
}

resource "terraform_data" "conn" {
  input = { password = var.db_password }
}
