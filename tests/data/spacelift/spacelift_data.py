# Mock data for Spacelift integration tests

# Account data
ACCOUNT_DATA = {
    "data": {
        "account": {
            "id": "test-account-123",
            "name": "Test Organization",
        },
    },
}

# Spaces data
SPACES_DATA = [
    {
        "id": "root-space",
        "name": "Root Space",
        "description": "Root space for testing",
        "parentSpace": None,
    },
    {
        "id": "child-space-1",
        "name": "Child Space 1",
        "description": "Child space for testing",
        "parentSpace": "root-space",
    },
]

# Users data
USERS_DATA = [
    {
        "id": "user-1",
        "username": "john.doe",
        "type": "HUMAN",
        "email": "john.doe@example.com",
    },
    {
        "id": "user-2",
        "username": "api-key-user",
        "type": "API_KEY",
        "email": None,
    },
]

# Stacks data
STACKS_DATA = [
    {
        "id": "stack-1",
        "name": "Production Stack",
        "description": "Main production infrastructure",
        "state": "ACTIVE",
        "administrative": True,
        "repository": "github.com/example/infra",
        "branch": "main",
        "projectRoot": "/terraform/prod",
        "space": "root-space",
    },
    {
        "id": "stack-2",
        "name": "Staging Stack",
        "description": "Staging environment",
        "state": "ACTIVE",
        "administrative": False,
        "repository": "github.com/example/infra",
        "branch": "staging",
        "projectRoot": "/terraform/staging",
        "space": "child-space-1",
    },
]

# Worker pools data
WORKER_POOLS_DATA = [
    {
        "id": "pool-1",
        "name": "Default Pool",
        "description": "Default worker pool",
        "type": "PUBLIC",
        "space": "root-space",
    },
    {
        "id": "pool-2",
        "name": "Private Pool",
        "description": "Private worker pool",
        "type": "PRIVATE",
        "space": "root-space",
    },
]

# Workers data
WORKERS_DATA = [
    {
        "id": "worker-1",
        "name": "worker-01",
        "status": "ACTIVE",
        "workerPool": "pool-1",
    },
    {
        "id": "worker-2",
        "name": "worker-02",
        "status": "ACTIVE",
        "workerPool": "pool-2",
    },
]

# Runs data
RUNS_DATA = [
    {
        "id": "run-1",
        "type": "PROPOSED",
        "state": "FINISHED",
        "commitSha": "abc123def456",
        "branch": "main",
        "createdAt": "2024-10-01T10:00:00Z",
        "startedAt": "2024-10-01T10:01:00Z",
        "finishedAt": "2024-10-01T10:05:00Z",
        "stack": "stack-1",
        "triggeredBy": "user-1",
        "worker": "worker-1",
    },
    {
        "id": "run-2",
        "type": "TRACKED",
        "state": "FINISHED",
        "commitSha": "def456ghi789",
        "branch": "staging",
        "createdAt": "2024-10-02T11:00:00Z",
        "startedAt": "2024-10-02T11:01:00Z",
        "finishedAt": "2024-10-02T11:10:00Z",
        "stack": "stack-2",
        "triggeredBy": "user-2",
        "worker": "worker-2",
    },
]

# Entities data - includes EC2 instances created by runs
ENTITIES_DATA = {
    "data": {
        "stacks": [
            {
                "entities": [
                    {
                        "type": "aws_instance",
                        "creator": {
                            "id": "run-1",
                        },
                        "updater": {
                            "id": "run-1",
                        },
                        "vendor": {
                            "__typename": "EntityVendorTerraform",
                            "terraform": {
                                "__typename": "TerraformResource",
                                "values": '{"id": "i-1234567890abcdef0", "ami": "ami-12345678", "instance_type": "t2.micro"}',
                            },
                        },
                    },
                    {
                        "type": "aws_instance",
                        "creator": {
                            "id": "run-1",
                        },
                        "updater": {
                            "id": "run-1",
                        },
                        "vendor": {
                            "__typename": "EntityVendorTerraform",
                            "terraform": {
                                "__typename": "TerraformResource",
                                "values": '{"id": "i-0987654321fedcba0", "ami": "ami-87654321", "instance_type": "t2.small"}',
                            },
                        },
                    },
                    {
                        "type": "aws_instance",
                        "creator": {
                            "id": "run-2",
                        },
                        "updater": {
                            "id": "run-2",
                        },
                        "vendor": {
                            "__typename": "EntityVendorTerraform",
                            "terraform": {
                                "__typename": "TerraformResource",
                                "values": '{"id": "i-abcdef1234567890a", "ami": "ami-11111111", "instance_type": "t3.medium"}',
                            },
                        },
                    },
                    # Non-EC2 entity - should be filtered out
                    {
                        "type": "aws_s3_bucket",
                        "creator": {
                            "id": "run-2",
                        },
                        "updater": {
                            "id": "run-2",
                        },
                        "vendor": {
                            "__typename": "EntityVendorTerraform",
                            "terraform": {
                                "__typename": "TerraformResource",
                                "values": '{"id": "my-test-bucket", "bucket": "my-test-bucket"}',
                            },
                        },
                    },
                ],
            },
        ],
    },
}

# EC2 instance data - mock existing EC2 instances in Neo4j
# These would typically be created by the AWS EC2 sync module
EC2_INSTANCES_DATA = [
    {
        "InstanceId": "i-1234567890abcdef0",
        "Region": "us-east-1",
        "InstanceType": "t2.micro",
        "State": "running",
    },
    {
        "InstanceId": "i-0987654321fedcba0",
        "Region": "us-east-1",
        "InstanceType": "t2.small",
        "State": "running",
    },
    {
        "InstanceId": "i-abcdef1234567890a",
        "Region": "us-west-2",
        "InstanceType": "t3.medium",
        "State": "running",
    },
]
