###############################################################################
# 第 02 讲实验 2-2：一个“可注入故障、可观测、可回滚”的最小工作负载
# 资源：IAM 角色（最小权限）、日志组（保留 1 天）、Lambda（arm64 / Python 3.14）、
#       告警（见 alarms.tf）。不创建 VPC、NAT、负载均衡器或公网 URL。
###############################################################################

data "archive_file" "fn" {
  type        = "zip"
  source_file = "${path.module}/src/handler.py"
  output_path = "${path.module}/build/handler.zip"
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "fn" {
  name               = "${var.name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

# 日志组由 Terraform 预先创建，所以函数只需要写日志流的权限——
# 比托管策略 AWSLambdaBasicExecutionRole（含 logs:CreateLogGroup on *）更小。
resource "aws_cloudwatch_log_group" "fn" {
  name              = "/aws/lambda/${var.name}"
  retention_in_days = 1
}

data "aws_iam_policy_document" "logs" {
  statement {
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.fn.arn}:*"]
  }
}

resource "aws_iam_role_policy" "logs" {
  name   = "write-own-log-group"
  role   = aws_iam_role.fn.id
  policy = data.aws_iam_policy_document.logs.json
}

# ---- 可选：AWS FIS Lambda 扩展（层 ARN 从 SSM 公共参数读取，避免写死版本号）----
locals {
  fis_bucket = coalesce(var.fis_config_bucket, "fis-config-bucket-not-set")
}
data "aws_ssm_parameter" "fis_layer" {
  count = var.enable_fis_extension ? 1 : 0
  name  = "/aws/service/fis/lambda-extension/AWS-FIS-extension-arm64/1.x.x"
}

data "aws_iam_policy_document" "fis_read" {
  count = var.enable_fis_extension ? 1 : 0
  statement {
    actions   = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::${local.fis_bucket}"]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["FisConfigs/*"]
    }
  }
  statement {
    actions   = ["s3:GetObject"]
    resources = ["arn:aws:s3:::${local.fis_bucket}/FisConfigs/*"]
  }
}

resource "aws_iam_role_policy" "fis_read" {
  count  = var.enable_fis_extension ? 1 : 0
  name   = "read-fis-fault-config"
  role   = aws_iam_role.fn.id
  policy = data.aws_iam_policy_document.fis_read[0].json
}

locals {
  fis_layers = var.enable_fis_extension ? [data.aws_ssm_parameter.fis_layer[0].insecure_value] : []
  fis_env = var.enable_fis_extension ? {
    AWS_FIS_CONFIGURATION_LOCATION     = "arn:aws:s3:::${local.fis_bucket}/FisConfigs/"
    AWS_LAMBDA_EXEC_WRAPPER            = "/opt/aws-fis/bootstrap"
    AWS_FIS_POLL_MAX_WAIT_MILLISECONDS = "2000"
  } : {}
}

resource "aws_lambda_function" "fn" {
  function_name    = var.name
  role             = aws_iam_role.fn.arn
  runtime          = "python3.14"
  architectures    = ["arm64"]
  handler          = "handler.handler"
  filename         = data.archive_file.fn.output_path
  source_code_hash = data.archive_file.fn.output_base64sha256
  timeout          = 3
  memory_size      = 128

  reserved_concurrent_executions = var.reserved_concurrency
  layers                         = local.fis_layers

  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.fn.name
  }

  environment {
    variables = merge({ FAIL_RATE = tostring(var.fail_rate) }, local.fis_env)
  }

  depends_on = [aws_iam_role_policy.logs]

}
