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
