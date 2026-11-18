# terraform init -backend=false && terraform test   —— mock provider，不连 AWS
mock_provider "aws" {
  override_during = plan
  mock_resource "aws_s3_bucket" {
    defaults = { arn = "arn:aws:s3:::a06-iam-sts-lab-x", id = "a06-iam-sts-lab-x" }
  }
  mock_resource "aws_iam_policy" {
    defaults = { arn = "arn:aws:iam::111122223333:policy/a06-boundary-logs-only" }
  }
}

variables {
  operator_arn = "arn:aws:iam::111122223333:user/ci-operator"
}

run "trust_names_exactly_one_operator" {
  command = plan

  assert {
    condition     = jsondecode(aws_iam_role.reader.assume_role_policy).Statement[0].Principal.AWS == "arn:aws:iam::111122223333:user/ci-operator"
    error_message = "信任策略只能信任指定的操作者，不能写 \"*\" 或整个账户。"
  }
}

run "baseline_reads_health_only" {
  command = plan

  assert {
    condition = (
      length(jsondecode(aws_iam_role_policy.reader.policy).Statement) == 1 &&
      jsondecode(aws_iam_role_policy.reader.policy).Statement[0].Resource == "arn:aws:s3:::a06-iam-sts-lab-x/logs/health.txt"
    )
    error_message = "基线只允许读取 logs/health.txt 这一个对象 ARN。"
  }
  assert {
    condition     = aws_iam_role.reader.permissions_boundary == null
    error_message = "默认不设置权限边界。"
  }
}

run "fix_adds_one_exact_statement" {
  command = plan
  variables {
    allow_report = true
  }

  assert {
    condition = (
      length(jsondecode(aws_iam_role_policy.reader.policy).Statement) == 2 &&
      jsondecode(aws_iam_role_policy.reader.policy).Statement[1].Resource == "arn:aws:s3:::a06-iam-sts-lab-x/reports/summary.csv"
    )
    error_message = "修复只增加一条精确到对象 ARN 的 Allow，而不是 s3:* 或 bucket/*。"
  }
}

run "boundary_caps_the_role" {
  command = plan
  variables {
    allow_report    = true
    enable_boundary = true
  }

  assert {
    condition     = aws_iam_role.reader.permissions_boundary == "arn:aws:iam::111122223333:policy/a06-boundary-logs-only"
    error_message = "启用后角色应挂上只允许 logs/* 的权限边界。"
  }
}

run "reject_session_arn_as_operator" {
  command = plan
  variables {
    operator_arn = "arn:aws:sts::111122223333:assumed-role/admin/alice"
  }
  expect_failures = [var.operator_arn]
}

run "bucket_denies_plain_http" {
  command = plan

  assert {
    condition     = jsondecode(aws_s3_bucket_policy.tls_only.policy).Statement[0].Condition.Bool["aws:SecureTransport"] == "false"
    error_message = "桶策略应拒绝非 HTTPS 请求。"
  }
}
