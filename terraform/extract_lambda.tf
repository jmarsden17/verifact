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
      {
        Effect = "Allow"

        Action = [
          "dynamodb:Scan",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]

        Resource = aws_dynamodb_table.c25-disinformation-dynamo.arn
      }
    ]
  })
}

resource "aws_lambda_function" "extract_lambda" {
    function_name = "c25_disinformation_extract"
    role = aws_iam_role.extract_lambda_role.arn
    package_type = "Image"
    image_uri = "" # Need image here

    memory_size = 512
    timeout = 120
}