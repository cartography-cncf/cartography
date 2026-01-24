# Test data for AWS Data Pipeline intel module
# Data shapes based on real AWS API responses with redacted account IDs

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789

# List Pipelines response - from list_pipelines API
LIST_PIPELINES_RESPONSE = {
    "pipelineIdList": [
        {"id": "df-1234567890", "name": "test-pipeline-1"},
        {"id": "df-0987654321", "name": "test-pipeline-2"},
    ],
}

# Describe Pipelines response - from describe_pipelines API
DESCRIBE_PIPELINES_RESPONSE = {
    "pipelineDescriptionList": [
        {
            "pipelineId": "df-1234567890",
            "name": "test-pipeline-1",
            "description": "Test pipeline for data processing",
            "pipelineState": "ACTIVE",
            "fields": [
                {
                    "key": "pipelineLogUri",
                    "stringValue": "s3://test-bucket/logs/",
                },
                {
                    "key": "role",
                    "stringValue": "arn:aws:iam::000000000000:role/DataPipelineDefaultRole",
                },
                {
                    "key": "resourceRole",
                    "stringValue": "arn:aws:iam::000000000000:role/DataPipelineDefaultResourceRole",
                },
            ],
        },
        {
            "pipelineId": "df-0987654321",
            "name": "test-pipeline-2",
            "description": "Another test pipeline",
            "pipelineState": "INACTIVE",
            "fields": [
                {
                    "key": "pipelineLogUri",
                    "stringValue": "s3://another-bucket/logs/",
                },
                {
                    "key": "role",
                    "stringValue": "arn:aws:iam::000000000000:role/DataPipelineCustomRole",
                },
            ],
        },
    ],
}

# Transformed pipeline data (what transform_datapipeline_pipelines produces)
TRANSFORMED_PIPELINES = [
    {
        "pipelineId": "df-1234567890",
        "name": "test-pipeline-1",
        "description": "Test pipeline for data processing",
        "status": "ACTIVE",
    },
    {
        "pipelineId": "df-0987654321",
        "name": "test-pipeline-2",
        "description": "Another test pipeline",
        "status": "INACTIVE",
    },
]
