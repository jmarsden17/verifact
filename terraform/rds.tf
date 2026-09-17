resource "aws_security_group" "c25-disinformation-rds-security-group" {
    name = "c25-disinformation-rds-security-group"
    description = "Allow inbound postgres traffic"
    vpc_id = data.aws_vpc.vpc.id

    ingress {
        description = "Postgres access"
        from_port = 5432
        to_port = 5432
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
}

resource "aws_db_instance" "c25-disinformation-rds" {
    identifier = "c25-disinformation-rds"
    instance_class = "db.t3.micro"
    engine = "postgres"
    engine_version = "17.10"
    username = var.db_user
    password = var.db_password
    allocated_storage = 10
    db_subnet_group_name = aws_db_subnet_group.public-subnets.name # ?????????????????????????????????
    vpc_security_group_ids = [aws_security_group.c25-disinformation-rds-security-group.id]
    publicly_accessible = true
    skip_final_snapshot = true
}