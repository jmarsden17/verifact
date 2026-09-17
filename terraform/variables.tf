variable "aws_region" {
  type = string
}

variable "aws_access_key_id" {
  type = string
  sensitive = true
}

variable "aws_secret_access_key" {
  type = string
  sensitive = true
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
  default     = "c25-ecs-cluster"
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "dashboard_password" {
  type        = string
  description = "Password for Streamlit dashboard access"
  sensitive   = true
}

variable "db_user" {
    description = "Database username"
    type = string
    sensitive = true
}

variable "db_password" {
    description = "Database password"
    type = string
    sensitive = true
}

variable "db_host" {
    description = "Database host"
    type = string
}

variable "db_name" {
    description = "Database name"
    type = string
}

variable "db_port" {
    description = "Database port"
    type = number
    default = 5432
}

variable "openai_api_key" {
    description = "OpenAI API key"
    type = string
    sensitive = true
}

variable "openai_base_url" {
    description = "OpenAI base URL"
    type = string
}

variable "firecrawl_api_key" {
    description = "Firecrawl API key"
    type = string
    sensitive = true
}