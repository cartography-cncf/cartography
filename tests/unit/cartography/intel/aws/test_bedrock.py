from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError

from cartography.intel.aws import bedrock


@pytest.mark.parametrize(
    "error_code",
    ["InternalServerException", "InternalServerErrorException"],
)
def test_get_knowledge_bases_raises_transient_region_failure_for_server_errors(
    error_code,
):
    # Arrange
    boto3_session = MagicMock()
    error = ClientError(
        {
            "Error": {
                "Code": error_code,
                "Message": "The server encountered an internal error",
            }
        },
        "ListKnowledgeBases",
    )
    paginator = boto3_session.client.return_value.get_paginator.return_value
    paginator.paginate.side_effect = error

    # Act and assert
    with pytest.raises(
        bedrock.knowledge_bases.BedrockKnowledgeBaseTransientRegionFailure
    ) as failure:
        bedrock.knowledge_bases.get_knowledge_bases(boto3_session, "us-east-1")

    assert failure.value.__cause__ is error
    boto3_session.client.assert_called_once()


def test_get_knowledge_bases_raises_transient_region_failure_for_endpoint_errors():
    # Arrange
    boto3_session = MagicMock()
    error = EndpointConnectionError(endpoint_url="https://bedrock-agent.example")
    boto3_session.client.side_effect = error

    # Act and assert
    with pytest.raises(
        bedrock.knowledge_bases.BedrockKnowledgeBaseTransientRegionFailure
    ) as failure:
        bedrock.knowledge_bases.get_knowledge_bases(boto3_session, "us-east-1")

    assert failure.value.__cause__ is error
    boto3_session.client.assert_called_once()


def test_get_knowledge_bases_preserves_access_denied_region_handling():
    # Arrange
    boto3_session = MagicMock()
    boto3_session.client.side_effect = ClientError(
        {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "Access denied",
            }
        },
        "ListKnowledgeBases",
    )

    # Act and assert
    assert bedrock.knowledge_bases.get_knowledge_bases(boto3_session, "us-east-1") == []
    boto3_session.client.assert_called_once()


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
