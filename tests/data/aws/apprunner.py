TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789

DESCRIBE_SERVICES = [
    {
        "ServiceName": "test-service-1",
        "ServiceId": "service-11111111111111111",
        "ServiceArn": (
            f"arn:aws:apprunner:{TEST_REGION}:{TEST_ACCOUNT_ID}:service/"
            "test-service-1/service-11111111111111111"
        ),
        "ServiceUrl": "test-service-1.us-east-1.awsapprunner.com",
        "Status": "RUNNING",
        "InstanceConfiguration": {
            "Cpu": "1024",
            "Memory": "2048",
            "InstanceRoleArn": (
                f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/AppRunnerInstanceRole"
            ),
        },
    },
    {
        "ServiceName": "test-service-2",
        "ServiceId": "service-22222222222222222",
        "ServiceArn": (
            f"arn:aws:apprunner:{TEST_REGION}:{TEST_ACCOUNT_ID}:service/"
            "test-service-2/service-22222222222222222"
        ),
        "ServiceUrl": "test-service-2.us-east-1.awsapprunner.com",
        "Status": "OPERATION_IN_PROGRESS",
        "InstanceConfiguration": {},
    },
]
