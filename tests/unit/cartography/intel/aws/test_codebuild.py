from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import EndpointConnectionError

from cartography.intel.aws import codebuild
from tests.data.aws.codebuild import GET_PROJECTS


def test_get_all_codebuild_projects_endpoint_connection_error():
    """Ensure EndpointConnectionError is handled gracefully."""
    # Arrange
    boto3_session = MagicMock()
    paginator = boto3_session.client.return_value.get_paginator.return_value
    paginator.paginate.side_effect = EndpointConnectionError(
        endpoint_url="https://codebuild.mx-central-1.amazonaws.com"
    )

    # Act
    result = codebuild.get_all_codebuild_projects(boto3_session, "mx-central-1")

    # Assert that we return nothing. In AWS region processing, endpoint connection
    # failures are often about service availability in that region, not client/server
    # network issues
    assert result == []


def test_get_all_codebuild_projects_connect_timeout_error():
    """Ensure ConnectTimeoutError is handled gracefully."""
    boto3_session = MagicMock()
    paginator = boto3_session.client.return_value.get_paginator.return_value
    paginator.paginate.side_effect = ConnectTimeoutError(
        endpoint_url="https://codebuild.ca-west-1.amazonaws.com"
    )

    result = codebuild.get_all_codebuild_projects(boto3_session, "ca-west-1")

    assert result == []


def test_get_all_codebuild_projects_invalid_token_error_raises():
    """Ensure non-skippable auth/config errors still surface."""
    boto3_session = MagicMock()
    paginator = boto3_session.client.return_value.get_paginator.return_value
    paginator.paginate.side_effect = ClientError(
        {
            "Error": {
                "Code": "InvalidToken",
                "Message": "token invalid",
            },
        },
        "ListProjects",
    )

    with pytest.raises(RuntimeError):
        codebuild.get_all_codebuild_projects(boto3_session, "us-east-1")


@patch.object(codebuild, "cleanup")
@patch.object(codebuild, "load_codebuild_projects")
@patch.object(codebuild, "get_all_codebuild_projects", return_value=GET_PROJECTS)
def test_sync_skips_unsupported_region(
    mock_get_all_codebuild_projects,
    mock_load_codebuild_projects,
    mock_cleanup,
):
    boto3_session = MagicMock()
    boto3_session.get_available_partitions.return_value = ["aws"]
    boto3_session.get_available_regions.return_value = ["us-east-1"]

    codebuild.sync(
        neo4j_session=MagicMock(),
        boto3_session=boto3_session,
        regions=["us-east-1", "ca-west-1"],
        current_aws_account_id="123456789012",
        update_tag=123,
        common_job_parameters={"UPDATE_TAG": 123, "AWS_ID": "123456789012"},
    )

    mock_get_all_codebuild_projects.assert_called_once_with(boto3_session, "us-east-1")
    mock_load_codebuild_projects.assert_called_once()
    mock_cleanup.assert_called_once()
