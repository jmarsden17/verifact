# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "dashboard_logs" {
  name              = "/ecs/c25-disinformation-dashboard"
  retention_in_days = 7
}

# IAM Trust Policy (Used by both Execution and Task Roles)
data "aws_iam_policy_document" "ecs_trust_policy_doc" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# --- Execution Role (Allows ECS agent to pull ECR image & write logs) ---
resource "aws_iam_role" "dashboard_execution_role" {
  name               = "c25-disinformation-dashboard-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_trust_policy_doc.json
}

# Attach standard AWS Managed Policy to guarantee ECR pull access (Fixes 403 Forbidden)
resource "aws_iam_role_policy_attachment" "dashboard_execution_managed_policy" {
  role       = aws_iam_role.dashboard_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# --- Task Role (Allows application code inside the container to access AWS services) ---
resource "aws_iam_role" "dashboard_task_role" {
  name               = "c25-disinformation-dashboard-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_trust_policy_doc.json
}

data "aws_iam_policy_document" "dashboard_task_permissions_doc" {
  statement {
    effect    = "Allow"
    actions   = ["ssm:GetParameters"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "dashboard_task_policy" {
  name   = "c25-disinformation-dashboard-task-policy"
  policy = data.aws_iam_policy_document.dashboard_task_permissions_doc.json
}

resource "aws_iam_role_policy_attachment" "dashboard_task_attachment" {
  role       = aws_iam_role.dashboard_task_role.name
  policy_arn = aws_iam_policy.dashboard_task_policy.arn
}

# --- ECS Task Definition ---
resource "aws_ecs_task_definition" "dashboard_task" {
  family                   = "c25-disinformation-dashboard-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.dashboard_execution_role.arn
  task_role_arn            = aws_iam_role.dashboard_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "c25-disinformation-dashboard"
      image     = "${aws_ecr_repository.c25-disinformation-ecr-dashboard.repository_url}:latest"
      essential = true

      portMappings = [
        {
          containerPort = 8501
          hostPort      = 8501
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "PYTHONPATH", value = "/app/frontend:/app" },
        { name = "PYTHONDONTWRITEBYTECODE", value = "1" },
        { name = "PYTHONUNBUFFERED", value = "1" },
        { name = "DASHBOARD_PASSWORD", value = var.dashboard_password },
        { name = "AWS_DEFAULT_REGION", value = var.aws_region },
        { name = "DB_HOST", value = var.db_host },
        { name = "DB_PORT", value = "5432" },
        { name = "DB_NAME", value = var.db_name },
        { name = "DB_USER", value = var.db_user },
        { name = "DB_PASSWORD", value = var.db_password }
      ]

      healthCheck = {
        command     = ["CMD-SHELL", "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:8501/_stcore/health\")'"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 15
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.dashboard_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "dashboard"
        }
      }
    }
  ])
}

# --- Security Group for Dashboard Streamlit Access ---
resource "aws_security_group" "dashboard_sg" {
  name        = "c25-disinformation-dashboard-sg"
  description = "Security group for Streamlit dashboard ECS task"
  vpc_id      = data.aws_vpc.vpc.id

  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- ECS Service Deployment ---
resource "aws_ecs_service" "dashboard_service" {
  name            = "c25-disinformation-dashboard-service"
  cluster         = data.aws_ecs_cluster.ecs-cluster.arn
  task_definition = aws_ecs_task_definition.dashboard_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_db_subnet_group.public-subnets.subnet_ids
    security_groups  = [aws_security_group.dashboard_sg.id]
    assign_public_ip = true
  }
}