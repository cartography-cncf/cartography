pipelineId1 = "df-1234567890ABCDEFGHI"
pipelineId2 = "df-0987654321JKLMNOPQR"

DESCRIBE_PIPELINES = [
    {
        "pipelineDescription": {
            "pipelineId": pipelineId1,
            "name": "MyDataPipeline",
            "fields": [
                {
                    "key": "name",
                    "stringValue": "MyDataPipeline"
                },
                {
                    "key": "description",
                    "stringValue": "Test pipeline for data processing"
                },
                {
                    "key": "@state",
                    "stringValue": "ACTIVE"
                },
                {
                    "key": "userId",
                    "stringValue": "AIDAEXAMPLEUSER123456789"
                },
                {
                    "key": "@pipelineState",
                    "stringValue": "SCHEDULED"
                },
                {
                    "key": "@creationTime",
                    "stringValue": "2023-01-15T10:30:00Z"
                },
                {
                    "key": "@version",
                    "stringValue": "1"
                }
            ]
        }
    },
    {
        "pipelineDescription": {
            "pipelineId": pipelineId2,
            "name": "ETLPipeline",
            "fields": [
                {
                    "key": "name",
                    "stringValue": "ETLPipeline"
                },
                {
                    "key": "description",
                    "stringValue": "ETL pipeline for data transformation"
                },
                {
                    "key": "@state",
                    "stringValue": "PENDING"
                },
                {
                    "key": "userId",
                    "stringValue": "AIDAEXAMPLEUSER987654321"
                },
                {
                    "key": "@pipelineState",
                    "stringValue": "FINISHED"
                },
                {
                    "key": "@creationTime",
                    "stringValue": "2023-02-20T14:45:00Z"
                },
                {
                    "key": "@version",
                    "stringValue": "2"
                }
            ]
        }
    }
]

LIST_PIPELINES = [
    {
        "id": pipelineId1,
        "name": "MyDataPipeline"
    },
    {
        "id": pipelineId2,
        "name": "ETLPipeline"
    }
]

# Test users with different permission sets for Data Pipeline privilege escalation testing
TEST_USERS = [
    {
        "user_id": "AIDAEXAMPLEUSER123456789",
        "user_name": "admin-user",
        "has_all_permissions": True,
        "permissions": [
            "iam:PassRole",
            "datapipeline:CreatePipeline",
            "datapipeline:PutPipelineDefinition",
            "datapipeline:ActivatePipeline"
        ]
    },
    {
        "user_id": "AIDAEXAMPLEUSER987654321",
        "user_name": "limited-user",
        "has_all_permissions": True,
        "permissions": [
            "iam:PassRole",
            "datapipeline:CreatePipeline",
            "datapipeline:PutPipelineDefinition",
            "datapipeline:ActivatePipeline"
        ]
    },
    {
        "user_id": "AIDAEXAMPLEUSER111222333",
        "user_name": "restricted-user",
        "has_all_permissions": False,
        "permissions": [
            "iam:PassRole",
            "datapipeline:CreatePipeline",
            "datapipeline:PutPipelineDefinition"
            # Missing: datapipeline:ActivatePipeline
        ]
    }
]
