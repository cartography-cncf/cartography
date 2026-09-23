from unittest.mock import MagicMock

import botocore.exceptions
import pytest

from cartography.intel.aws import bedrock


@pytest.mark.parametrize(
    ("error_code", "expected_exception"),
    [
        (
            "InternalServerException",
            bedrock.knowledge_bases.BedrockKnowledgeBaseRegionServerError,
        ),
        ("AccessDeniedException", botocore.exceptions.ClientError),
    ],
)
def test_bedrock_knowledge_base_region_error_classification(
    error_code, expected_exception
):
    # Arrange
    def raises_error():
        raise botocore.exceptions.ClientError(
            {
                "Error": {
                    "Code": error_code,
                    "Message": "The server encountered an internal error",
                }
            },
            "ListKnowledgeBases",
        )

    wrapped = (
        bedrock.knowledge_bases._reraise_bedrock_knowledge_base_region_server_errors(
            raises_error
        )
    )

    # Act and assert
    with pytest.raises(expected_exception):
        wrapped()


@pytest.mark.parametrize("agent_regions", [[], ["ap-southeast-4", "us-west-2"]])
def test_sync_filters_regions_per_bedrock_resource(mocker, agent_regions):
    # Arrange
    boto3_session = MagicMock()
    boto3_session.get_partition_for_region.return_value = "aws"
    boto3_session.get_available_regions.side_effect = lambda service, **_: {
        "bedrock": ["us-west-1", "ap-southeast-4", "us-west-2"],
        "bedrock-agent": agent_regions,
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
        regions=["us-west-1", "ap-southeast-4", "us-west-2"],
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
            ["us-west-1", "ap-southeast-4", "us-west-2"],
            "123456789012",
            123,
            common_job_parameters,
        )
    sync_mocks[bedrock.knowledge_bases].assert_called_once_with(
        neo4j_session,
        boto3_session,
        ["us-west-2"],
        "123456789012",
        123,
        common_job_parameters,
    )
    sync_mocks[bedrock.agents].assert_called_once_with(
        neo4j_session,
        boto3_session,
        ["ap-southeast-4", "us-west-2"],
        "123456789012",
        123,
        common_job_parameters,
    )
