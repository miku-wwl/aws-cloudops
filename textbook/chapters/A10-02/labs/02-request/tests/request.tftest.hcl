# terraform init && terraform test   —— 离线，不需要 provider 与凭证
variables {
  request = {
    control_tower_parameters = {
      AccountEmail              = "sandbox-07@example.invalid"
      AccountName               = "sandbox-07"
      ManagedOrganizationalUnit = "Sandbox"
      SSOUserEmail              = "owner@example.invalid"
      SSOUserFirstName          = "Example"
      SSOUserLastName           = "Owner"
    }
    account_tags = { CostCenter = "training", Owner = "platform-team" }
    change_management_parameters = {
      change_requested_by = "Platform Team"
      change_reason       = "第 18 讲教学示例，不得推送到真实仓库"
    }
    custom_fields               = { desired_baseline = "extra-logging" }
    account_customizations_name = "sandbox-customizations"
  }
}

run "valid_request_is_accepted" {
  command = plan

  assert {
    condition     = jsondecode(output.request).account_customizations_name == "sandbox-customizations"
    error_message = "合法请求应原样传给 AFT 模块。"
  }
}

run "nested_ou_syntax_is_accepted" {
  command = plan
  variables {
    request = merge(var.request, {
      control_tower_parameters = merge(var.request.control_tower_parameters, { ManagedOrganizationalUnit = "Dev (ou-ab12-3cd4ef56)" })
    })
  }
}

run "missing_costcenter_tag_is_rejected" {
  command = plan
  variables {
    request = merge(var.request, { account_tags = { Owner = "platform-team" } })
  }
  expect_failures = [var.request]
}

run "real_email_domain_is_rejected" {
  command = plan
  variables {
    request = merge(var.request, {
      control_tower_parameters = merge(var.request.control_tower_parameters, { AccountEmail = "someone@gmail.com" })
    })
  }
  expect_failures = [var.request]
}

run "bad_ou_syntax_is_rejected" {
  command = plan
  variables {
    request = merge(var.request, {
      control_tower_parameters = merge(var.request.control_tower_parameters, { ManagedOrganizationalUnit = "Dev/ou-ab12-3cd4ef56" })
    })
  }
  expect_failures = [var.request]
}

run "unknown_customization_template_is_rejected" {
  command = plan
  variables {
    request = merge(var.request, { account_customizations_name = "sandbox-customisations" })
  }
  expect_failures = [var.request]
}
