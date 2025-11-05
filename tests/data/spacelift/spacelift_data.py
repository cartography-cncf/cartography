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

# Spaces data - returned from GET_SPACES_QUERY
SPACES_DATA = {
    "data": {
        "spaces": [
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
        ],
    },
}

# Stacks data - returned from GET_STACKS_QUERY
STACKS_DATA = {
    "data": {
        "stacks": [
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
        ],
    },
}

# Worker pools data - returned from GET_WORKER_POOLS_QUERY
WORKER_POOLS_DATA = {
    "data": {
        "workerPools": [
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
        ],
    },
}

# Workers data - returned from GET_WORKERS_QUERY (nested under workerPools)
WORKERS_DATA = {
    "data": {
        "workerPools": [
            {
                "id": "pool-1",
                "workers": [
                    {
                        "id": "worker-1",
                        "status": "ACTIVE",
                    },
                ],
            },
            {
                "id": "pool-2",
                "workers": [
                    {
                        "id": "worker-2",
                        "status": "ACTIVE",
                    },
                ],
            },
        ],
    },
}

# Runs data - returned from GET_RUNS_QUERY nested under stacks
RUNS_DATA = {
    "data": {
        "stacks": [
            {
                "id": "stack-1",
                "runs": [
                    {
                        "id": "run-1",
                        "type": "PROPOSED",
                        "state": "FINISHED",
                        "commit": {
                            "hash": "abc123def456",
                            "authorLogin": "johndoe",
                            "authorName": "John Doe",
                            "message": "Add production infrastructure",
                            "timestamp": "2024-10-01T09:00:00Z",
                            "url": "https://github.com/example/infra/commit/abc123def456",
                        },
                        "branch": "main",
                        "createdAt": "2024-10-01T10:00:00Z",
                        "finished": "2024-10-01T10:05:00Z",
                        "triggeredBy": "john.doe@example.com",
                    },
                ],
            },
            {
                "id": "stack-2",
                "runs": [
                    {
                        "id": "run-2",
                        "type": "TRACKED",
                        "state": "FINISHED",
                        "commit": {
                            "hash": "def456ghi789",
                            "authorLogin": "janedoe",
                            "authorName": "Jane Doe",
                            "message": "Update staging environment",
                            "timestamp": "2024-10-02T10:00:00Z",
                            "url": "https://github.com/example/infra/commit/def456ghi789",
                        },
                        "branch": "staging",
                        "createdAt": "2024-10-02T11:00:00Z",
                        "finished": "2024-10-02T11:10:00Z",
                        "triggeredBy": "vcs/commit",
                    },
                ],
            },
        ],
    },
}

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
                                "values": '{"id": "i-01", "ami": "ami-12345678", "instance_type": "c4.large"}',
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
                                "values": '{"id": "i-02", "ami": "ami-87654321", "instance_type": "c4.large"}',
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
                                "values": '{"id": "i-03", "ami": "ami-11111111", "instance_type": "r4.large"}',
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
        "InstanceId": "i-01",
        "Region": "us-east-1",
        "InstanceType": "c4.large",
        "State": "running",
    },
    {
        "InstanceId": "i-02",
        "Region": "us-east-1",
        "InstanceType": "c4.large",
        "State": "running",
    },
    {
        "InstanceId": "i-03",
        "Region": "us-east-1",
        "InstanceType": "r4.large",
        "State": "running",
    },
]

# CloudTrail data for EC2 ownership tracking
# This represents CloudTrail events from Athena showing Spacelift runs interacting with EC2 instances
# Data format matches what get_ec2_ownership returns after parsing JSON from S3
# Real Athena data has these fields as strings (Hive struct format), but our parsing handles both
CLOUDTRAIL_EC2_OWNERSHIP_DATA = [
    # Three events from run-1 affecting instance i-01234567 (tests bug fix - each event preserved)
    {
        "eventid": "event-uuid-1",
        "useridentity": "arn=arn:aws:sts::123456789012:assumed-role/spacelift-role/run-1@spacelift.io",
        "eventtime": "2024-01-01T10:00:00Z",
        "eventname": "DescribeInstances",
        "account": "000000000000",
        "awsregion": "us-east-1",
        "resources": [
            {"ARN": "arn:aws:ec2:us-east-1:000000000000:instance/i-01234567"}
        ],
    },
    {
        "eventid": "event-uuid-2",
        "useridentity": "arn=arn:aws:sts::123456789012:assumed-role/spacelift-role/run-1@spacelift.io",
        "eventtime": "2024-01-01T11:00:00Z",
        "eventname": "RunInstances",
        "account": "000000000000",
        "awsregion": "us-east-1",
        "responseelements": {"instancesSet": {"items": [{"instanceId": "i-01234567"}]}},
    },
    {
        "eventid": "event-uuid-3",
        "useridentity": "arn=arn:aws:sts::123456789012:assumed-role/spacelift-role/run-1@spacelift.io",
        "eventtime": "2024-01-01T12:00:00Z",
        "eventname": "DescribeInstances",
        "account": "000000000000",
        "awsregion": "us-east-1",
        "resources": [
            {"ARN": "arn:aws:ec2:us-east-1:000000000000:instance/i-01234567"}
        ],
    },
    # One event from run-2 affecting instance i-89abcdef
    {
        "eventid": "event-uuid-4",
        "useridentity": "arn=arn:aws:sts::123456789012:assumed-role/spacelift-role/run-2@spacelift.io",
        "eventtime": "2024-01-01T13:00:00Z",
        "eventname": "DescribeInstances",
        "account": "000000000000",
        "awsregion": "us-east-1",
        "resources": [
            {"ARN": "arn:aws:ec2:us-east-1:000000000000:instance/i-89abcdef"}
        ],
    },
]
