from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError

from cartography.intel.aws import bedrock
from tests.data.aws.bedrock import TEST_ACCOUNT_ID
from tests.data.aws.bedrock import TEST_REGION


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


def _make_agent(foundation_model, guardrail_configuration=None):
    agent = {
        "agentId": "TEST123",
        "agentArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/TEST123",
        "foundationModel": foundation_model,
        "knowledgeBaseSummaries": [],
        "actionGroupDetails": [],
    }
    if guardrail_configuration is not None:
        agent["guardrailConfiguration"] = guardrail_configuration
    return agent


_MODEL_ARN_KEYS = ("foundation_model_arn", "custom_model_arn", "provisioned_model_arn")


@pytest.mark.parametrize(
    "foundation_model, expected_key, expected_value",
    [
        pytest.param(
            # Bare model ID is converted to a foundation model ARN
            "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "foundation_model_arn",
            f"arn:aws:bedrock:{TEST_REGION}::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
            id="bare_id",
        ),
        pytest.param(
            # Foundation model ARN is preserved
            f"arn:aws:bedrock:{TEST_REGION}::foundation-model/anthropic.claude-v2",
            "foundation_model_arn",
            f"arn:aws:bedrock:{TEST_REGION}::foundation-model/anthropic.claude-v2",
            id="fm_arn",
        ),
        pytest.param(
            # Custom model ARN sets custom_model_arn
            f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:custom-model/my-model",
            "custom_model_arn",
            f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:custom-model/my-model",
            id="custom_arn",
        ),
        pytest.param(
            # Provisioned throughput ARN sets provisioned_model_arn
            f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:provisioned-model/my-pt",
            "provisioned_model_arn",
            f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:provisioned-model/my-pt",
            id="provisioned_arn",
        ),
    ],
)
def test_transform_agents_foundation_model_union_type(
    foundation_model,
    expected_key,
    expected_value,
):
    """
    The agent foundationModel field can be a bare model ID, a foundation model ARN,
    a custom model ARN or a provisioned throughput ARN. Exactly one of the model ARN
    keys is set on the transformed agent.
    """
    # Arrange
    agents = [_make_agent(foundation_model)]

    # Act
    result = bedrock.agents.transform_agents(agents, TEST_REGION, TEST_ACCOUNT_ID)

    # Assert
    assert result[0][expected_key] == expected_value
    for other_key in _MODEL_ARN_KEYS:
        if other_key != expected_key:
            assert other_key not in result[0]


def test_transform_agents_guardrail_id_to_arn():
    """Test that guardrail ID is converted to ARN without version suffix."""
    # Arrange
    agents = [
        _make_agent(
            "anthropic.claude-v2",
            guardrail_configuration={
                "guardrailIdentifier": "abc123",
                "guardrailVersion": "DRAFT",
            },
        )
    ]

    # Act
    result = bedrock.agents.transform_agents(agents, TEST_REGION, TEST_ACCOUNT_ID)

    # Assert - version should NOT be included in ARN
    assert result[0]["guardrail_arn"] == (
        f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:guardrail/abc123"
    )


def test_transform_agents_guardrail_arn_preserved():
    """Test that guardrail ARN is preserved when already provided."""
    # Arrange
    guardrail_arn = f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:guardrail/xyz789"
    agents = [
        _make_agent(
            "anthropic.claude-v2",
            guardrail_configuration={
                "guardrailIdentifier": guardrail_arn,
                "guardrailVersion": "1",
            },
        )
    ]

    # Act
    result = bedrock.agents.transform_agents(agents, TEST_REGION, TEST_ACCOUNT_ID)

    # Assert
    assert result[0]["guardrail_arn"] == guardrail_arn
