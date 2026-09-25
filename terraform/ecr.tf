resource "aws_ecr_repository" "c25-disinformation-ecr-dashboard" {
	name = "c25-disinformation-ecr-dashboard"
	image_tag_mutability = "MUTABLE"
	
	image_scanning_configuration {
		scan_on_push = true
	}
}

resource "aws_ecr_repository" "c25-disinformation-ecr-query" {
	name = "c25-disinformation-ecr-query"
	image_tag_mutability = "MUTABLE"
	
	image_scanning_configuration {
		scan_on_push = true
	}
}

resource "aws_ecr_repository" "c25-disinformation-ecr-claim-verification" {
	name = "c25-disinformation-ecr-claim-verification"
	image_tag_mutability = "MUTABLE"
	
	image_scanning_configuration {
		scan_on_push = true
	}
}

resource "aws_ecr_repository" "c25-disinformation-ecr-transform-load" {
	name = "c25-disinformation-ecr-transform-load"
	image_tag_mutability = "MUTABLE"
	
	image_scanning_configuration {
		scan_on_push = true
	}
}