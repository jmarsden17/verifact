resource "aws_iam_role" "transform_load_lambda_role" {
  name = "c25-disinformation-transform-load-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Effect = "Allow"

      Principal = {
        Service = "lambda.amazonaws.com"
      }

      Action = "sts:AssumeRole"
    }]
  })
}


resource "aws_iam_role_policy" "transform_load_lambda_policy" {
  role = aws_iam_role.transform_load_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]

        Resource = "*"
      }]
  })
}

resource "aws_iam_role_policy_attachment" "load_vpc_access" {
  role       = aws_iam_role.transform_load_lambda_role.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_lambda_function" "transform_load_lambda" {
    function_name = "c25_disinformation_transform_load"
    role = aws_iam_role.transform_load_lambda_role.arn
    package_type = "Image"
    image_uri = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c25-disinformation-ecr-transform-load:latest" # Need image here

    memory_size = 512
    timeout = 120

    environment {
        variables = {
            OPENAI_API_KEY = var.openai_api_key
            OPENAI_BASE_URL = var.openai_base_url
            DB_HOST         = var.db_host
            DB_NAME         = var.db_name
            DB_USER         = var.db_user
            DB_PASSWORD     = var.db_password
            DB_PORT         = var.db_port
        }
    }
}