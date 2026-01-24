from cartography.intel.aws.datapipeline import transform_datapipeline_pipelines
from tests.data.aws.datapipeline import DESCRIBE_PIPELINES_RESPONSE
from tests.data.aws.datapipeline import TRANSFORMED_PIPELINES

TEST_REGION = "us-east-1"


def test_transform_datapipeline_pipelines():
    """Test transform_datapipeline_pipelines function with mock API response data."""
    # Use the full mock API response data
    pipeline_data = DESCRIBE_PIPELINES_RESPONSE["pipelineDescriptionList"]
    transformed = transform_datapipeline_pipelines(pipeline_data, TEST_REGION)

    # Should transform 2 pipelines
    assert len(transformed) == 2

    # Expected first pipeline
    expected_pipeline_1 = TRANSFORMED_PIPELINES[0]
    assert transformed[0] == expected_pipeline_1

    # Expected second pipeline
    expected_pipeline_2 = TRANSFORMED_PIPELINES[1]
    assert transformed[1] == expected_pipeline_2


def test_transform_datapipeline_pipelines_empty():
    """Test transform_datapipeline_pipelines with empty input."""
    transformed = transform_datapipeline_pipelines([], TEST_REGION)
    assert transformed == []


def test_transform_datapipeline_pipelines_missing_fields():
    """Test transform_datapipeline_pipelines handles missing optional fields."""
    pipeline_data = [
        {
            "pipelineId": "df-test123",
            "name": "test-pipeline",
            # Missing description and pipelineState
        },
    ]
    transformed = transform_datapipeline_pipelines(pipeline_data, TEST_REGION)

    assert len(transformed) == 1
    assert transformed[0]["pipelineId"] == "df-test123"
    assert transformed[0]["name"] == "test-pipeline"
    assert transformed[0]["description"] is None
    assert transformed[0]["status"] is None
