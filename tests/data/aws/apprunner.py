DESCRIBE_SERVICES = [
    {
        "ServiceName": "my-service",
        "ServiceId": "abc123",
        "ServiceArn": "arn:aws:apprunner:us-east-1:123456789012:service/my-service/abc123",
        "ServiceUrl": "abc123.us-east-1.awsapprunner.com",
        "CreatedAt": "2023-01-01T00:00:00Z",
        "UpdatedAt": "2023-01-02T00:00:00Z",
        "Status": "RUNNING",
        "SourceConfiguration": {
            "ImageRepository": {
                "ImageIdentifier": "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo:latest",
                "ImageRepositoryType": "ECR",
                "ImageConfiguration": {},
            },
            "AutoDeploymentsEnabled": True,
            "AuthenticationConfiguration": {
                "AccessRoleArn": "arn:aws:iam::1234:role/cartography-read-only",
            },
        },
        "InstanceConfiguration": {
            "Cpu": "1 vCPU",
            "Memory": "2 GB",
            "InstanceRoleArn": "arn:aws:iam::1234:role/cartography-service",
        },
        "NetworkConfiguration": {
            "EgressConfiguration": {
                "EgressType": "DEFAULT",
            },
            "IngressConfiguration": {
                "IsPubliclyAccessible": True,
            },
        },
    },
    {
        "ServiceName": "my-other-service",
        "ServiceId": "def456",
        "ServiceArn": "arn:aws:apprunner:us-east-1:123456789012:service/my-other-service/def456",
        "ServiceUrl": "def456.us-east-1.awsapprunner.com",
        "CreatedAt": "2023-02-01T00:00:00Z",
        "UpdatedAt": "2023-02-02T00:00:00Z",
        "Status": "RUNNING",
        "SourceConfiguration": {
            "ImageRepository": {
                "ImageIdentifier": "123456789012.dkr.ecr.us-east-1.amazonaws.com/other-repo:latest",
                "ImageRepositoryType": "ECR",
                "ImageConfiguration": {},
            },
            "AutoDeploymentsEnabled": False,
            "AuthenticationConfiguration": {
                "AccessRoleArn": "arn:aws:iam::1234:role/cartography-read-only",
            },
        },
        "InstanceConfiguration": {
            "Cpu": "2 vCPU",
            "Memory": "4 GB",
            "InstanceRoleArn": "arn:aws:iam::1234:role/cartography-service",
        },
        "NetworkConfiguration": {
            "EgressConfiguration": {
                "EgressType": "VPC",
            },
            "IngressConfiguration": {
                "IsPubliclyAccessible": False,
            },
        },
    },
    {
        "ServiceName": "my-code-service",
        "ServiceId": "ghi789",
        "ServiceArn": "arn:aws:apprunner:us-east-1:123456789012:service/my-code-service/ghi789",
        "ServiceUrl": "ghi789.us-east-1.awsapprunner.com",
        "CreatedAt": "2023-03-01T00:00:00Z",
        "UpdatedAt": "2023-03-02T00:00:00Z",
        "Status": "RUNNING",
        "SourceConfiguration": {
            "CodeRepository": {
                "RepositoryUrl": "https://github.com/example/my-code-service",
                "SourceCodeVersion": {"Type": "BRANCH", "Value": "main"},
                "CodeConfiguration": {},
            },
            "AutoDeploymentsEnabled": True,
        },
        "InstanceConfiguration": {
            "Cpu": "1 vCPU",
            "Memory": "2 GB",
            "InstanceRoleArn": "arn:aws:iam::1234:role/cartography-service",
        },
        "NetworkConfiguration": {
            "EgressConfiguration": {
                "EgressType": "DEFAULT",
            },
            "IngressConfiguration": {
                "IsPubliclyAccessible": True,
            },
        },
    },
]
