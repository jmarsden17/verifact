# Terraform

This folder defines the AWS infrastructure for the Disinformation Verifier: the RDS database, container registries, the three pipeline Lambdas, and the ECS Fargate service that runs the Streamlit dashboard.

## What it creates

| File | Resources |
|---|---|
| `main.tf` | Terraform Cloud backend (organisation and workspace are both `disinformation-verifier`), the AWS provider, and lookups for the existing ECS cluster, DB subnet group and VPC |
| `rds.tf` | A security group for Postgres (port 5432) and the `c25-disinformation-rds` instance: PostgreSQL 17.10, `db.t3.micro`, 10 GB, publicly accessible, no final snapshot |
| `extract_lambda.tf` | IAM role and policy, and the `c25_disinformation_extract` Lambda (container image, 512 MB, 120 s timeout). It runs in the VPC with the OpenAI and `DB_*` environment variables |
| `claim_verification_lambda.tf` | IAM role and policy, and the `c25_disinformation_claim_verification` Lambda (512 MB, 120 s). Environment: OpenAI variables and `FIRECRAWL_API_KEY` |
| `transform_load_lambda.tf` | IAM role and policy, and the `c25_disinformation_transform_load` Lambda (512 MB, 120 s). Environment: OpenAI variables only |
| `frontend.tf` | ECR repo for the dashboard, CloudWatch log group (7 day retention), execution and task IAM roles, a Fargate task definition (0.5 vCPU, 1 GB, port 8501, health check on `/_stcore/health`), a security group, and an ECS service with a public IP |
| `ecr.tf` | ECR repositories `c25-disinformation-ecr-dashboard`, `c25-disinformation-ecr-query` and `c25-disinformation-ecr-claim-verification`, with image scanning on push |
| `dynamodb.tf` | An on-demand DynamoDB table `c25-disinformation-dynamo` (hash key `tags`, range key `timestamp`). It is left over from the original design and nothing in the code uses it |
| `variables.tf` | The input variables (below) |

The Lambda IAM roles only allow CloudWatch Logs. The extract Lambda also gets `AWSLambdaVPCAccessExecutionRole`.

## Before you start

- Terraform installed.
- A Terraform Cloud account with access to the `disinformation-verifier` organisation and workspace (set in `main.tf`). Run `terraform login` first.
- AWS credentials that can create the resources above.
- Docker, to build and push images.
- These must already exist in the AWS account, because Terraform only looks them up:
  - an ECS cluster (default name `c25-ecs-cluster`, or set `ecs_cluster_name`)
  - a DB subnet group called `c25-public-subnet`

## Variables

Set these as Terraform Cloud workspace variables, or in a local `terraform.tfvars` (which is git-ignored). Don't commit secrets.

| Variable | Type | Default | Description |
|---|---|---|---|
| `aws_region` | string | none | AWS region |
| `aws_access_key_id` | string, sensitive | none | AWS access key for the provider |
| `aws_secret_access_key` | string, sensitive | none | AWS secret key for the provider |
| `ecs_cluster_name` | string | `c25-ecs-cluster` | Existing ECS cluster for the dashboard |
| `vpc_id` | string | none | Declared but not used (the VPC is found through the subnet group) |
| `vpc_subnet_ids` | list(string) | none | Subnets for the extract Lambda |
| `rds_sg_id` | string | none | Security group for the extract Lambda's VPC access |
| `db_host` | string | none | Database host passed to the extract Lambda |
| `db_name` | string | none | Database name passed to the extract Lambda |
| `db_user` | string, sensitive | none | Database username (also used to create the RDS instance) |
| `db_password` | string, sensitive | none | Database password (also used to create the RDS instance) |
| `db_port` | number | `5432` | Database port |
| `openai_api_key` | string, sensitive | none | LLM API key |
| `openai_base_url` | string | none | LLM API base URL |
| `firecrawl_api_key` | string, sensitive | none | Firecrawl API key |
| `dashboard_password` | string, sensitive | none | Dashboard login password |

Example `terraform.tfvars` with placeholders:

```hcl
aws_region         = "eu-west-2"
ecs_cluster_name   = "c25-ecs-cluster"
vpc_id             = "vpc-xxxxxxxx"
vpc_subnet_ids     = ["subnet-aaaaaaaa", "subnet-bbbbbbbb"]
rds_sg_id          = "sg-xxxxxxxx"
db_host            = "<rds-endpoint>"
db_name            = "disinformation"
db_user            = "<username>"
openai_base_url    = "<base url>"
# Pass the secrets (AWS keys, db_password, openai_api_key, firecrawl_api_key,
# dashboard_password) through Terraform Cloud sensitive variables or TF_VAR_* environment variables.
```

## Usage

```bash
cd terraform
terraform init
terraform plan
terraform apply      # create the cloud services
terraform destroy    # remove everything
```

Once the RDS instance exists, load the schema. This creates the `disinformation` database and seeds it (see [database/README.md](../database/README.md)):

```bash
psql -h <rds-endpoint> -p 5432 -U <db_user> postgres -f ../database/schema.sql
```

## Deploying images

The Lambdas and the dashboard are container images pulled from ECR.

1. Log in to ECR:

```bash
aws ecr get-login-password --region <region> \
  | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
```

2. Dashboard. Build from the repository root, because the Dockerfile needs the whole repo. The ECS service pulls the `latest` tag from `c25-disinformation-dashboard-repo`.

```bash
docker build --platform linux/amd64 -f frontend/Dockerfile -t <account-id>.dkr.ecr.<region>.amazonaws.com/c25-disinformation-dashboard-repo:latest .
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/c25-disinformation-dashboard-repo:latest
```

Then force a new deployment so the service picks up the new image:

```bash
aws ecs update-service --cluster c25-ecs-cluster --service c25-disinformation-dashboard-service --force-new-deployment
```

3. Lambdas. Build each one from inside its own folder, push it to an ECR repo, and put the image URI into that Lambda's `image_uri` in Terraform. They are currently empty strings marked `# Need image here`.

```bash
cd pipeline/extract_claims      # or verify_claims, or transform_load
docker build --platform linux/amd64 -t <ecr-repo-url>:latest .
docker push <ecr-repo-url>:latest
```

`terraform apply` will fail on the Lambdas until `image_uri` is filled in. The dashboard's public IP is shown on the ECS task in the AWS console, because the service uses `assign_public_ip = true`.

## Security

Things to fix before this is used with real data:

- RDS is public and open. It has `publicly_accessible = true` and the security group allows port 5432 from `0.0.0.0/0`. Limit it to the Lambda and dashboard security groups (or your own IP while setting up) and make the instance private.
- The dashboard port 8501 is open to the internet. Put it behind a load balancer with HTTPS, or limit the source range. The only protection right now is the app password.
- Secrets are plain environment variables (DB password, OpenAI and Firecrawl keys, dashboard password) in the Lambda config and the ECS task definition. That means they show up in the console and in Terraform state. Move them to AWS Secrets Manager or SSM Parameter Store. The ECS task role already allows `ssm:GetParameters` on `*`, which should be narrowed to specific parameters.
- The provider uses long-lived access keys passed in as variables. An assumed role or OIDC from Terraform Cloud would be better.
- `skip_final_snapshot = true` means `terraform destroy` deletes the database with no backup.
- The Lambda roles only write logs, which is a good starting point to keep.

## Known gaps

- The Lambda `image_uri` values are empty.
- Only the verify Lambda has a matching ECR repo in `ecr.tf` (`claim-verification`). There are none for the extract or transform / load images. There is also an `ecr-query` repo with no Lambda (the query Lambda is still a stub), and two dashboard repos (one in `ecr.tf` and one in `frontend.tf`).
- The transform / load Lambda has no database variables (`DATABASE_*`) and no VPC config, but `load.py` needs both to reach RDS.
- The verify Lambda gets `FIRECRAWL_API_KEY`, but the code reads `API_KEY`.
- The DynamoDB table is not used.
- `vpc_id` is declared but never referenced.