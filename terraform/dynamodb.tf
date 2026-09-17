resource "aws_dynamodb_table" "c25-disinformation-dynamo" {
    name = "c25-disinformation-dynamo"
    billing_mode = "PAY_PER_REQUEST"
    hash_key = "tags"
    range_key = "timestamp"

    attribute {
        name = "tags"
        type = "S"
    }

    attribute {
        name = "timestamp"
        type = "S"
    }
}
