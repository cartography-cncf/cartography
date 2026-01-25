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
