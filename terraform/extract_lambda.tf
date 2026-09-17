resource "aws_iam_role" "extract_lambda_role" {
  name = "c25-gabi-extract-lambda-role"

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


resource "aws_iam_role_policy" "extract_lambda_policy" {
  role = aws_iam_role.extract_lambda_role.id

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
      },
      ]
  })
}

resource "aws_iam_role_policy_attachment" "vpc_access" {
  role       = aws_iam_role.extract_lambda_role.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_lambda_function" "extract_lambda" {
    function_name = "c25_disinformation_extract"
    role = aws_iam_role.extract_lambda_role.arn
    package_type = "Image"
    image_uri = "" # Need image here

    memory_size = 512
    timeout = 120
    
      vpc_config {
        subnet_ids         = data.aws_db_subnet_group.public-subnets.name
        security_group_ids = [aws_security_group.lambda_sg.id]
      }
    

      environment {
        variables = {
          OPENAI_API_KEY  = var.openai_api_key
          OPENAI_BASE_URL = var.openai_base_url
          DB_HOST         = var.db_host
          DB_NAME         = var.db_name
          DB_USER         = var.db_user
          DB_PASSWORD     = var.db_password
          DB_PORT         = var.db_port
        }

  }
}

