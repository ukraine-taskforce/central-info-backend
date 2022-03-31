variable "reigon" {
  description = "Reigon"
  type        = string
}

variable "env_name" {
  description = "Enviornment Name"
  type        = string
}

variable "domain_name" {
  description = "Root Domain Name"
  type        = string
}

variable "api_subdomain" {
  description = "API Subdomain"
  type        = string
}

variable "telegram_token" {
  description = "Telegram generated token"
  type        = string
  sensitive   = true
}

variable "lambda_info_bot_key" {
  description = "S3 Object Key for Bot's Lambda function"
  type        = string
  default     = "central-info-bot.zip"
}

variable "lambda_info_key" {
  description = "S3 Object Key for Web App's Lambda function"
  type        = string
  default     = "central-info.zip"
}

variable "acl" {
  description = "S3 bucket ACL"
  type        = string
  default     = "private"
}
