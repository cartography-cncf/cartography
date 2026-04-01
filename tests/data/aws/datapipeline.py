GET_DATAPIPELINE_PIPELINE_ID_LIST = [
    {
        "id": "df-06372391ZG65EXAMPLE",
        "name": "production-etl-pipeline",
    },
    {
        "id": "df-01234567AB89EXAMPLE",
        "name": "analytics-pipeline",
    },
]


GET_DATAPIPELINE_PIPELINE_DETAILS = [
    {
        "pipelineId": "df-06372391ZG65EXAMPLE",
        "name": "production-etl-pipeline",
        "description": "ETL pipeline for production data ingestion",
        "uniqueId": "2f34a51b-9f90-4fb2-a6aa-ef7d53f6b20a",
        "fields": [
            {"key": "@pipelineState", "stringValue": "ACTIVE"},
            {"key": "@healthStatus", "stringValue": "HEALTHY"},
        ],
    },
    {
        "pipelineId": "df-01234567AB89EXAMPLE",
        "name": "analytics-pipeline",
        "description": "Pipeline for daily analytics workloads",
        "uniqueId": "eea34c4a-5b79-4f8d-b9cb-a6012204f890",
        "fields": [
            {"key": "@pipelineState", "stringValue": "INACTIVE"},
        ],
    },
]
