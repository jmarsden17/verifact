
resource "aws_iam_role" "step_function_role" {
  name = "c25-disinformation-step-function-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "step_function_role_policy" {
  role       = aws_iam_role.step_function_role.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaRole"
}

resource "aws_iam_role_policy" "invoke_lambdas" {
  role = aws_iam_role.step_function_role.id

  policy = jsonencode({
    "Version":"2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "lambda:InvokeFunction"
        ],
        "Resource": "arn:aws:lambda:us-east-1:123456789012:function:myFunction"
      }
    ]
  })
}

resource "aws_sfn_state_machine" "c25_disinformation" {
  name     = "c25-disinformation-state-machine"
  role_arn = aws_iam_role.step_function_role.arn

  definition = <<EOF
{
  "Comment": "Claim verification workflow",
  "QueryLanguage": "JSONata",
  "StartAt": "Extract",
  "States": {
    "Extract": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Arguments": {
        "FunctionName": "arn:aws:lambda:eu-west-2:129033205317:function:c25_disinformation_extract:$LATEST",
        "Payload": "{% $states.input %}"
      },
      "Output": "{% $states.result.Payload %}",
      "Retry": [
        {
          "ErrorEquals": [
            "Lambda.ServiceException",
            "Lambda.AWSLambdaException",
            "Lambda.SdkClientException",
            "Lambda.TooManyRequestsException"
          ],
          "IntervalSeconds": 1,
          "MaxAttempts": 3,
          "BackoffRate": 2,
          "JitterStrategy": "FULL"
        }
      ],
      "Next": "Split"
    },
    "Split": {
      "Type": "Pass",
      "Assign": {
        "skipped": "{% $states.input.body.skipped %}"
      },
      "Output": {
        "statusCode": 200,
        "body": "{% $states.input.body.to_process %}"
      },
      "Next": "Choice"
    },
    "Choice": {
      "Type": "Choice",
      "Choices": [
        {
          "Condition": "{% $count($states.input.body) = 0 %}",
          "Next": "Pass"
        }
      ],
      "Default": "Parallel"
    },
    "Pass": {
      "Type": "Pass",
      "Output": "{% [] %}",
      "Next": "Transform/Load"
    },
    "Parallel": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "Full Fact",
          "States": {
            "Full Fact": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "Arguments": {
                "FunctionName": "arn:aws:lambda:eu-west-2:129033205317:function:c25_disinformation_claim_verification:$LATEST",
                "Payload": "{% $merge([$states.input, {'source_url': 'fullfact.org'},{'source_name': 'Full Fact'}]) %}"
              },
              "Output": "{% $states.result.Payload %}",
              "Retry": [
                {
                  "ErrorEquals": [
                    "Lambda.ServiceException",
                    "Lambda.AWSLambdaException",
                    "Lambda.SdkClientException",
                    "Lambda.TooManyRequestsException"
                  ],
                  "IntervalSeconds": 1,
                  "MaxAttempts": 3,
                  "BackoffRate": 2,
                  "JitterStrategy": "FULL"
                }
              ],
              "End": true
            }
          }
        },
        {
          "StartAt": "BBC Verify",
          "States": {
            "BBC Verify": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "Arguments": {
                "FunctionName": "arn:aws:lambda:eu-west-2:129033205317:function:c25_disinformation_claim_verification:$LATEST",
                "Payload": "{% $merge([$states.input, {'source_url': 'bbc.co.uk/news/articles'},{'source_name': 'BBC Verify'}]) %}"
              },
              "Output": "{% $states.result.Payload %}",
              "Retry": [
                {
                  "ErrorEquals": [
                    "Lambda.ServiceException",
                    "Lambda.AWSLambdaException",
                    "Lambda.SdkClientException",
                    "Lambda.TooManyRequestsException"
                  ],
                  "IntervalSeconds": 1,
                  "MaxAttempts": 3,
                  "BackoffRate": 2,
                  "JitterStrategy": "FULL"
                }
              ],
              "End": true
            }
          }
        },
        {
          "StartAt": "Reuters Fact Check",
          "States": {
            "Reuters Fact Check": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "Arguments": {
                "FunctionName": "arn:aws:lambda:eu-west-2:129033205317:function:c25_disinformation_claim_verification:$LATEST",
                "Payload": "{% $merge([$states.input, {'source_url': 'reuters.com/fact-check'},{'source_name': 'Reuters Fact Check'}]) %}"
              },
              "Output": "{% $states.result.Payload %}",
              "Retry": [
                {
                  "ErrorEquals": [
                    "Lambda.ServiceException",
                    "Lambda.AWSLambdaException",
                    "Lambda.SdkClientException",
                    "Lambda.TooManyRequestsException"
                  ],
                  "IntervalSeconds": 1,
                  "MaxAttempts": 3,
                  "BackoffRate": 2,
                  "JitterStrategy": "FULL"
                }
              ],
              "End": true
            }
          }
        }
      ],
      "Next": "Transform/Load"
    },
    "Transform/Load": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Arguments": {
        "FunctionName": "arn:aws:lambda:eu-west-2:129033205317:function:c25_disinformation_transform_load:$LATEST",
        "Payload": "{% { 'results': $states.input, 'skipped': $skipped } %}"
      },
      "Output": "{% $states.result.Payload %}",
      "Retry": [
        {
          "ErrorEquals": [
            "Lambda.ServiceException",
            "Lambda.AWSLambdaException",
            "Lambda.SdkClientException",
            "Lambda.TooManyRequestsException"
          ],
          "IntervalSeconds": 1,
          "MaxAttempts": 3,
          "BackoffRate": 2,
          "JitterStrategy": "FULL"
        }
      ],
      "End": true
    }
  }
}
EOF

}