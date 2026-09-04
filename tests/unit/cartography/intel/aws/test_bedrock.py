from unittest.mock import MagicMock

from cartography.intel.aws import bedrock


def test_sync_skips_us_west_1_for_bedrock_agent_apis(mocker):
    # Arrange
    boto3_session = MagicMock()
    boto3_session.get_partition_for_region.return_value = "aws"
    boto3_session.get_available_regions.side_effect = lambda service, **_: {
        "bedrock": ["us-west-1", "us-west-2"],
        "bedrock-agent": [],
    }[service]
    sync_mocks = {
        module: mocker.patch.object(module, "sync")
        for module in (
            bedrock.agents,
            bedrock.custom_models,
            bedrock.foundation_models,
            bedrock.guardrails,
            bedrock.knowledge_bases,
            bedrock.provisioned_model_throughput,
        )
    }
    neo4j_session = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": 123,
        "AWS_ID": "123456789012",
    }

    # Act
    bedrock.sync(
        neo4j_session=neo4j_session,
        boto3_session=boto3_session,
        regions=["us-west-1", "us-west-2"],
        current_aws_account_id="123456789012",
        update_tag=123,
        common_job_parameters=common_job_parameters,
    )

    # Assert
    for module in (
        bedrock.custom_models,
        bedrock.foundation_models,
        bedrock.guardrails,
        bedrock.provisioned_model_throughput,
    ):
        sync_mocks[module].assert_called_once_with(
            neo4j_session,
            boto3_session,
            ["us-west-1", "us-west-2"],
            "123456789012",
            123,
            common_job_parameters,
        )
    for module in (bedrock.knowledge_bases, bedrock.agents):
        sync_mocks[module].assert_called_once_with(
            neo4j_session,
            boto3_session,
            ["us-west-2"],
            "123456789012",
            123,
            common_job_parameters,
        )
