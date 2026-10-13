"""Shared kwargs for AWS sync function tests (unit and integration)."""

from typing import Any
from unittest import mock

import neo4j

TEST_REGIONS = ["us-east-1", "us-west-2"]
TEST_UPDATE_TAG = 123456789
GRAPH_JOB_PARAMETERS = {"UPDATE_TAG": TEST_UPDATE_TAG}


def make_aws_sync_test_kwargs(
    neo4j_session: neo4j.Session,
    mock_boto3_session: mock.MagicMock,
) -> dict[str, Any]:
    """
    Returns a dummy dict of kwargs to use for AWS sync functions.
    The keys of this dict are also used to ensure that parameter names for all sync functions are standardized; see
    `test_standardize_aws_sync_kwargs`.
    Note: aioboto3_session is NOT included here because it's only used by ecr:image_layers, which has a different
    signature from the standard AWS sync functions.
    """
    return {
        "neo4j_session": neo4j_session,
        "boto3_session": mock_boto3_session(),
        "current_aws_account_id": "1234",
        "update_tag": TEST_UPDATE_TAG,
        "regions": TEST_REGIONS,
        "common_job_parameters": GRAPH_JOB_PARAMETERS,
    }
