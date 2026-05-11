LINEAGE = "b5be69d6-88bc-b354-fd59-b5971742d6ea"
TEST_ACCOUNT_ID = "181047820466"
TEST_REGION = "us-east-1"

TEST_EKS_CLUSTER_NAME = "test-eks-cluster"
TEST_EKS_CLUSTER_ARN = (
    f"arn:aws:eks:{TEST_REGION}:{TEST_ACCOUNT_ID}:cluster/{TEST_EKS_CLUSTER_NAME}"
)

TEST_LAMBDA_NAME = "test-lambda"
TEST_LAMBDA_ARN = (
    f"arn:aws:lambda:{TEST_REGION}:{TEST_ACCOUNT_ID}:function:{TEST_LAMBDA_NAME}"
)

TEST_SQS_QUEUE_URL = (
    f"https://sqs.{TEST_REGION}.amazonaws.com/{TEST_ACCOUNT_ID}/test-queue"
)
TEST_SQS_QUEUE_ARN = f"arn:aws:sqs:{TEST_REGION}:{TEST_ACCOUNT_ID}:test-queue"

TEST_DYNAMODB_TABLE_NAME = "test-table"
TEST_DYNAMODB_TABLE_ARN = (
    f"arn:aws:dynamodb:{TEST_REGION}:{TEST_ACCOUNT_ID}:table/{TEST_DYNAMODB_TABLE_NAME}"
)

TEST_KMS_KEY_ID = "mrk-1234567890abcdef0"
TEST_KMS_KEY_ARN = f"arn:aws:kms:{TEST_REGION}:{TEST_ACCOUNT_ID}:key/{TEST_KMS_KEY_ID}"

SAMPLE_STATE_FILE: dict = {
    "version": 4,
    "terraform_version": "1.14.2",
    "serial": 100,
    "lineage": LINEAGE,
    "outputs": {
        "cluster_name": {
            "value": "enbuild_eks_dev",
            "type": "string",
        },
        "kms_key_id": {
            "value": "super-secret-key-id",
            "type": "string",
            "sensitive": True,
        },
    },
    "resources": [
        {
            "mode": "data",
            "type": "aws_caller_identity",
            "name": "current",
            "provider": 'provider["registry.terraform.io/hashicorp/aws"]',
            "instances": [
                {
                    "schema_version": 0,
                    "attributes": {
                        "account_id": TEST_ACCOUNT_ID,
                        "arn": f"arn:aws:iam::{TEST_ACCOUNT_ID}:user/test@example.com",
                        "id": TEST_ACCOUNT_ID,
                        "user_id": "AIDASUJ2KQCZBY4QSI6VS",
                    },
                    "sensitive_attributes": [],
                },
            ],
        },
        {
            "mode": "managed",
            "type": "aws_iam_policy",
            "name": "sops",
            "provider": 'provider["registry.terraform.io/hashicorp/aws"]',
            "instances": [
                {
                    "schema_version": 0,
                    "attributes": {
                        "arn": f"arn:aws:iam::{TEST_ACCOUNT_ID}:policy/test-kms",
                        "id": f"arn:aws:iam::{TEST_ACCOUNT_ID}:policy/test-kms",
                        "name": "test-kms",
                        "policy": '{"Version":"2012-10-17"}',
                        "tags": {"Owner": "test@example.com"},
                        "tags_all": {"Owner": "test@example.com", "Project": "TEST"},
                    },
                    "sensitive_attributes": [],
                    "dependencies": [
                        "data.aws_caller_identity.current",
                    ],
                },
            ],
        },
        {
            "mode": "managed",
            "type": "aws_s3_bucket",
            "name": "logs",
            "provider": 'provider["registry.terraform.io/hashicorp/aws"]',
            "instances": [
                {
                    "schema_version": 0,
                    "attributes": {
                        "id": "my-test-logs-bucket",
                        "bucket": "my-test-logs-bucket",
                        "arn": "arn:aws:s3:::my-test-logs-bucket",
                        "tags": {},
                    },
                    "sensitive_attributes": [],
                    "dependencies": ["data.aws_caller_identity.current"],
                },
            ],
        },
        {
            "mode": "managed",
            "type": "aws_eks_cluster",
            "name": "main",
            "provider": 'provider["registry.terraform.io/hashicorp/aws"]',
            "instances": [
                {
                    "schema_version": 0,
                    "attributes": {
                        "id": TEST_EKS_CLUSTER_NAME,
                        "arn": TEST_EKS_CLUSTER_ARN,
                        "name": TEST_EKS_CLUSTER_NAME,
                    },
                    "sensitive_attributes": [],
                },
            ],
        },
        {
            "mode": "managed",
            "type": "aws_lambda_function",
            "name": "handler",
            "provider": 'provider["registry.terraform.io/hashicorp/aws"]',
            "instances": [
                {
                    "schema_version": 0,
                    "attributes": {
                        "id": TEST_LAMBDA_NAME,
                        "arn": TEST_LAMBDA_ARN,
                        "function_name": TEST_LAMBDA_NAME,
                    },
                    "sensitive_attributes": [],
                },
            ],
        },
        {
            "mode": "managed",
            "type": "aws_sqs_queue",
            "name": "jobs",
            "provider": 'provider["registry.terraform.io/hashicorp/aws"]',
            "instances": [
                {
                    "schema_version": 0,
                    "attributes": {
                        "id": TEST_SQS_QUEUE_URL,
                        "arn": TEST_SQS_QUEUE_ARN,
                        "name": "test-queue",
                    },
                    "sensitive_attributes": [],
                },
            ],
        },
        {
            "mode": "managed",
            "type": "aws_dynamodb_table",
            "name": "state",
            "provider": 'provider["registry.terraform.io/hashicorp/aws"]',
            "instances": [
                {
                    "schema_version": 0,
                    "attributes": {
                        "id": TEST_DYNAMODB_TABLE_NAME,
                        "arn": TEST_DYNAMODB_TABLE_ARN,
                        "name": TEST_DYNAMODB_TABLE_NAME,
                    },
                    "sensitive_attributes": [],
                },
            ],
        },
        {
            "mode": "managed",
            "type": "aws_kms_key",
            "name": "main",
            "provider": 'provider["registry.terraform.io/hashicorp/aws"]',
            "instances": [
                {
                    "schema_version": 0,
                    "attributes": {
                        "id": TEST_KMS_KEY_ARN,
                        "arn": TEST_KMS_KEY_ARN,
                        "key_id": TEST_KMS_KEY_ID,
                    },
                    "sensitive_attributes": [],
                },
            ],
        },
    ],
}
