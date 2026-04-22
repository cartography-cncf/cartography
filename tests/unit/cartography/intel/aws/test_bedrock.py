from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.aws import bedrock


@patch.object(bedrock.provisioned_model_throughput, "sync")
@patch.object(bedrock.agents, "sync")
@patch.object(bedrock.knowledge_bases, "sync")
@patch.object(bedrock.guardrails, "sync")
@patch.object(bedrock.custom_models, "sync")
@patch.object(bedrock.foundation_models, "sync")
@patch.object(bedrock, "filter_regions_to_supported_service_regions")
def test_bedrock_sync_filters_regions_by_endpoint_family(
    mock_filter_regions,
    mock_foundation_models_sync,
    mock_custom_models_sync,
    mock_guardrails_sync,
    mock_knowledge_bases_sync,
    mock_agents_sync,
    mock_provisioned_model_throughput_sync,
):
    mock_filter_regions.side_effect = [
        (["us-east-1"], ["eu-west-3"]),
        (["us-east-1", "us-west-2"], ["eu-west-3"]),
    ]
    boto3_session = MagicMock()
    neo4j_session = MagicMock()
    common_job_parameters = {"UPDATE_TAG": 1, "AWS_ID": "123456789012"}

    bedrock.sync(
        neo4j_session=neo4j_session,
        boto3_session=boto3_session,
        regions=["us-east-1", "us-west-2", "eu-west-3"],
        current_aws_account_id="123456789012",
        update_tag=1,
        common_job_parameters=common_job_parameters,
    )

    assert mock_filter_regions.call_args_list == [
        call(boto3_session, "bedrock", ["us-east-1", "us-west-2", "eu-west-3"]),
        call(
            boto3_session,
            "bedrock-agent",
            ["us-east-1", "us-west-2", "eu-west-3"],
        ),
    ]
    for patched_sync in (
        mock_foundation_models_sync,
        mock_custom_models_sync,
        mock_guardrails_sync,
        mock_provisioned_model_throughput_sync,
    ):
        patched_sync.assert_called_once_with(
            neo4j_session,
            boto3_session,
            ["us-east-1"],
            "123456789012",
            1,
            common_job_parameters,
        )

    for patched_sync in (
        mock_knowledge_bases_sync,
        mock_agents_sync,
    ):
        patched_sync.assert_called_once_with(
            neo4j_session,
            boto3_session,
            ["us-east-1", "us-west-2"],
            "123456789012",
            1,
            common_job_parameters,
        )
