# 阶段 4：停止管理但不销毁（例如把资源移交给另一个工程）
removed {
  from = module.orders.terraform_data.release
  lifecycle {
    destroy = false
  }
}
