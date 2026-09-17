terraform {
    cloud {
        organization = "disinformation-verifier"
        workspaces {
            name = "disinformation-verifier"
        }
    }
}

provider "aws" {
    region = var.aws_region
    access_key = var.aws_access_key_id
    secret_key = var.aws_secret_access_key
}

data "aws_ecs_cluster" "ecs-cluster" {
    cluster_name = var.ecs_cluster_name
}

data "aws_vpc" "vpc" {
  id = data.aws_db_subnet_group.public-subnets.vpc_id
}

data   "aws_db_subnet_group" "public-subnets" {
    name = "c25-public-subnet"
}