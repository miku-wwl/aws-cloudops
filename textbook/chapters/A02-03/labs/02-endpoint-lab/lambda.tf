###############################################################################
# VPC 内的探针函数：与实验 5-1 同一份 layers.py，逐层报告 DNS / TCP / TLS / HTTP / API
###############################################################################
data "archive_file" "probe" {
  type        = "zip"
  source_file = "${path.module}/../01-layers/layers.py"
  output_path = "${path.module}/build/probe.zip"
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

resource "aws_iam_role" "probe" {
  name               = "a05-probe-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

# 进入 VPC 需要创建/删除 ENI 的权限（含写日志）
resource "aws_iam_role_policy_attachment" "vpc_access" {
  role       = aws_iam_role.probe.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

data "aws_iam_policy_document" "read_two_things" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.lab.arn}/hello.txt"]
  }
  statement {
    actions   = ["ssm:GetParameter"]
    resources = [aws_ssm_parameter.hello.arn]
  }
}

resource "aws_iam_role_policy" "read_two_things" {
  name   = "read-lab-object-and-parameter"
  role   = aws_iam_role.probe.id
  policy = data.aws_iam_policy_document.read_two_things.json
}

resource "aws_cloudwatch_log_group" "probe" {
  name              = "/aws/lambda/a05-endpoint-probe"
  retention_in_days = 1
}

resource "aws_lambda_function" "probe" {
  function_name    = "a05-endpoint-probe"
  role             = aws_iam_role.probe.arn
  runtime          = "python3.14"
  architectures    = ["arm64"]
  handler          = "layers.handler"
  filename         = data.archive_file.probe.output_path
  source_code_hash = data.archive_file.probe.output_base64sha256
  timeout          = 20
  memory_size      = 256

  vpc_config {
    subnet_ids         = [aws_subnet.private.id]
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      BUCKET = aws_s3_bucket.lab.id
      KEY    = aws_s3_object.hello.key
      PARAM  = aws_ssm_parameter.hello.name
    }
  }

  depends_on = [aws_iam_role_policy_attachment.vpc_access, aws_cloudwatch_log_group.probe]
}

output "probe_function_name" {
  value = aws_lambda_function.probe.function_name
}

output "ssm_endpoint_dns" {
  value = aws_vpc_endpoint.ssm.dns_entry
}

output "s3_prefix_list_id" {
  value = aws_vpc_endpoint.s3.prefix_list_id
}
