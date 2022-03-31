provider "aws" {
  reigon = var.reigon
}

locals {
  api_domain_name = join(".", [var.api_subdomain, var.domain_name])
}

# For cloud connections
module "vpc" {
  source      = "terraform-aws-modules/vpc/aws"
  enable_ipv6 = true
  name        = join("-", [var.env_name, var.reigon, "vpc"])
  cidr        = "10.0.0.0/16" 
  azs         = [join([var.reigon, "a"]), join([var.reigon, "b"]), join(var.reigon, "c")]

  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  one_nat_gateway_per_az = false
}


module "acm" {
  source = "terraform-aws-modules/acm/aws"

  domain_name = var.domain_name
  zone_id     = data.cloudflare_zone.this.id

  subject_alternative_names = [
    local.api_domain_name
  ]

  create_route53_records  = false
  validation_record_fqdns = cloudflare_record.validation.*.hostname
}

resource "cloudflare_record" "validation" {
  count = length(module.acm.distinct_domain_names)

  zone_id = data.cloudflare_zone.this.id
  name    = element(module.acm.validation_domains, count.index)["resource_record_name"]
  type    = element(module.acm.validation_domains, count.index)["resource_record_type"]
  value   = replace(element(module.acm.validation_domains, count.index)["resource_record_value"], "/.$/", "")
  ttl     = 60
  proxied = false

  allow_overwrite = true
}

data "cloudflare_zone" "this" {
  name = var.domain_name
}

# Backend API Gateway
resource "aws_apigatewayv2_api" "ugt_gw" {
  name          = join("-", [var.env_name, var.region, "api-gateway"])
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = [join("", ["https://", var.domain_name])]
    allow_methods = ["POST"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_stage" "ugt_gw_stage" {
  api_id = aws_apigatewayv2_api.ugt_gw.id

  name        = "live"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.ugt_api_gw.arn

    format = jsonencode({
      requestId               = "$context.requestId"
      sourceIp                = "$context.identity.sourceIp"
      requestTime             = "$context.requestTime"
      protocol                = "$context.protocol"
      httpMethod              = "$context.httpMethod"
      resourcePath            = "$context.resourcePath"
      routeKey                = "$context.routeKey"
      status                  = "$context.status"
      responseLength          = "$context.responseLength"
      integrationErrorMessage = "$context.integrationErrorMessage"
    }
    )
  }
}

resource "aws_cloudwatch_log_group" "ugt_api_gw" {
  name = "/aws/ugt_api_gw/${aws_apigatewayv2_api.ugt_gw.name}"

  retention_in_days = 30
}

# Bot webhook API
resource "aws_lambda_permission" "bot_webhook" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bot.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.ugt_gw.execution_arn}/*/*"
}

resource "aws_apigatewayv2_integration" "bot_webhook" {
  api_id = aws_apigatewayv2_api.ugt_gw.id

  integration_uri    = aws_lambda_function.bot.invoke_arn
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "bot_webhook" {
  api_id = aws_apigatewayv2_api.ugt_gw.id

  route_key = "POST /${random_id.both_path.hex}/webhook"
  target    = "integrations/$aws_apigatewayv2_integration.bot_webhook.id}"
}

resource "random_id" "both_path" {
  byte_length = 16
}

# Bot send_results API
resource "aws_lambda_permission" "bot_send_results" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bot.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.ugt_gw.execution_arn}/*/*"
}

resource "aws_apigatewayv2_integration" "bot_send_results" {
  api_id = aws_apigatewayv2_api.ugt_gw.id

  integration_uri    = aws_lambda_function.bot.invoke_arn
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "bot_send_results" {
  api_id = aws_apigatewayv2_api.ugt_gw.id
  route_key = "POST /${random_id.both_path.hex}/send_results"
  target    = "integrations/${aws_apigatewayv2_integration.send_results.id}"
}

# Info API (for webapp)
resource "aws_lambda_permission" "info" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.info.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.ugt_gw.execution_arn}/*/*"
}

resource "aws_apigatewayv2_integration" "get_info" {
  api_id = aws_apigatewayv2_api.ugt_gw.id

  integration_uri    = aws_lambda_function.info.invoke_arn
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "get_info" {
  api_id = aws_apigatewayv2_api.ugt_gw.id

  route_key = "GET /api/v1/incident"
  target    = "integrations/${aws_apigatewayv2_integration.get_info.id}"
}

# Lambda functions
# Bot API
resource "aws_lambda_function" "info_bot" {
  function_name = "PostBotMessage"

  s3_bucket = aws_s3_bucket.ugt_lambda_states.id
  s3_key    = var.lambda_info_bot_key

  timeout = 30
  handler = "index.handler"
  runtime = "nodejs14.x"

  role = aws_iam_role.fetch_info_policy.arn

  environment {
    variables = {
      domain                    = aws_apigatewayv2_api.ugt_gw.api_endpoint
      path_key                  = random_id.both_path.hex
      token_parameter           = aws_secretsmanager_secret.telegram_token.arn
      table_name                = aws_dynamodb_table.central-info.name
    }
  }
}

resource "aws_cloudwatch_log_group" "info_bot" {
  name = "/aws/lambda/${aws_lambda_function.info_bot.function_name}"

  retention_in_days = 30
}

# Info API
resource "aws_lambda_function" "info" {
  function_name = "GetInfo"

  s3_bucket = aws_s3_bucket.ugt_lambda_states.id
  s3_key    = var.lambda_info_key

  runtime = "nodejs14.x"
  handler = "index.handler"

  role = aws_iam_role.fetch_info_policy.arn

  environment {
    variables = {
      table_name  = aws_dynamodb_table.central-info.name
    }
  }
}

resource "aws_cloudwatch_log_group" "info" {
  name = "/aws/lambda/${aws_lambda_function.info.function_name}"

  retention_in_days = 30
}

# DynamoDB
resource "aws_dynamodb_table" "central-info" {
  name         = join("-", [var.env_name, var.region, "dynamodb-central-info"])
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "resource_id"

  attribute {
    name = "resource_id"
    type = "S"
  }
}

# IAM roles
resrouce "aws_iam_policy" "fetch_info_policy" {
  name        = "fetch_info_policy"
  description = "fetch_info_policy"

  policy = <<EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
          "dynamodb:BatchGetItem"
        ],
        "Effect": "Allow",
        "Resource": "${aws_dynamodb_table.central-info.arn}"
      }
    ]
  }
  EOF
}

resource "aws_iam_role" "fetch_info_policy" {
  name = "fetch_info_policy"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
  EOF
}

# Secrets
resource "aws_secretsmanager_secret" "telegram_token" {
  name = "lambda/telegram-bot-client/token"
}

resource "aws_secretsmanager_secret_version" "telegram_token" {
  secret_id = aws_secretsmanager_secret.telegram_token.id
  secret_string = var.telegram_token
}

# Backend Domain
resource "aws_apigatewayv2_domain_name" "backend" {
  domain_name = local.api_domain_name

  domain_name_configuration {
    certificate_arn = module.acm.acm_certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

resource "cloudflare_record" "backend" {
  zone_id = data.cloudflare_zone.this.id
  name    = var.api_subdomain
  type    = "CNAME"
  value   = aws_apigatewayv2_domain_name.backend.domain_name_configuration[0].target_domain_name
  ttl     = 1
  proxied = true

  allow_overwrite = true
}

resource "aws_apigatewayv2_api_mapping" "live" {
  api_id          = aws_apigatewayv2_api.ugt_gw.id
  domain_name     = aws_apigatewayv2_domain_name.backend.id
  stage           = aws_apigatewayv2_stage.ugt_gw_stage.id
  api_mapping_key = aws_apigatewayv2_stage.ugt_gw_stage.name
}
