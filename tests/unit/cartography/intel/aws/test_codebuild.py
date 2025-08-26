from unittest.mock import MagicMock

from botocore.exceptions import EndpointConnectionError

from cartography.intel.aws import codebuild


def test_get_all_codebuild_projects_endpoint_connection_error():
    """Ensure EndpointConnectionError is handled gracefully."""
    boto3_session = MagicMock()
    paginator = boto3_session.client.return_value.get_paginator.return_value
    paginator.paginate.side_effect = EndpointConnectionError(endpoint_url="https://codebuild.mx-central-1.amazonaws.com")

    result = codebuild.get_all_codebuild_projects(boto3_session, "mx-central-1")

    assert result == []
