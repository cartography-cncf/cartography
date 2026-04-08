from cartography.intel.aws.datapipeline import transform_datapipeline_pipelines
from tests.data.aws.datapipeline import GET_DATAPIPELINE_PIPELINE_DETAILS

TEST_REGION = "eu-west-1"
TEST_ACCOUNT_ID = "000000000000"


def test_transform_datapipeline_pipelines():
    transformed = transform_datapipeline_pipelines(
        GET_DATAPIPELINE_PIPELINE_DETAILS,
        TEST_REGION,
        TEST_ACCOUNT_ID,
    )

    assert len(transformed) == 2
    assert transformed[0] == {
        "Id": "arn:aws:datapipeline:eu-west-1:000000000000:pipeline/df-06372391ZG65EXAMPLE",
        "Arn": "arn:aws:datapipeline:eu-west-1:000000000000:pipeline/df-06372391ZG65EXAMPLE",
        "PipelineId": "df-06372391ZG65EXAMPLE",
        "Name": "production-etl-pipeline",
        "Description": "ETL pipeline for production data ingestion",
        "UniqueId": "2f34a51b-9f90-4fb2-a6aa-ef7d53f6b20a",
        "State": "ACTIVE",
        "HealthStatus": "HEALTHY",
        "Region": "eu-west-1",
    }
    assert transformed[1]["HealthStatus"] is None


def test_transform_datapipeline_pipelines_skips_entries_without_pipeline_id():
    transformed = transform_datapipeline_pipelines(
        [{"name": "broken-pipeline", "fields": []}],
        TEST_REGION,
        TEST_ACCOUNT_ID,
    )

    assert transformed == []
