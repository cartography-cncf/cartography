from copy import deepcopy
from unittest.mock import MagicMock
from unittest.mock import patch

import boto3
from botocore.stub import Stubber

import cartography.intel.aws.securityhub
from tests.data.aws.securityhub import GET_HUB
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.securityhub,
    "get_hub",
    return_value=deepcopy(GET_HUB),
)
def test_sync_hub(mock_get_hub, neo4j_session):
    """
    Ensure that sync() creates AWSSecurityHub nodes and links them to the AWS account.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    cartography.intel.aws.securityhub.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(
        neo4j_session,
        "AWSSecurityHub",
        ["id", "subscribed_at", "auto_enable_controls"],
    ) == {
        (
            "arn:aws:securityhub:us-east-1:000000000000:hub/default",
            1606993517,
            True,
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSSecurityHub",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "arn:aws:securityhub:us-east-1:000000000000:hub/default"),
    }


def test_sync_hub_when_describe_hub_is_denied(neo4j_session):
    """
    A role without securityhub:DescribeHub skips Security Hub instead of stopping the
    account sync, and keeps the hub that an earlier sync loaded.
    """
    # Arrange
    neo4j_session.run("MATCH (n:AWSSecurityHub) DETACH DELETE n")
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    with patch.object(
        cartography.intel.aws.securityhub, "get_hub", return_value=deepcopy(GET_HUB)
    ):
        cartography.intel.aws.securityhub.sync(
            neo4j_session,
            MagicMock(),
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        )
    seeded = check_nodes(neo4j_session, "AWSSecurityHub", ["id"])
    new_update_tag = TEST_UPDATE_TAG + 1
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, new_update_tag)
    client = boto3.session.Session().client(
        "securityhub",
        region_name=TEST_REGION,
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )
    stubber = Stubber(client)
    stubber.add_client_error("describe_hub", service_error_code="AccessDeniedException")
    stubber.activate()
    boto3_session = MagicMock()
    boto3_session.client.return_value = client

    # Act
    cartography.intel.aws.securityhub.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        new_update_tag,
        {"UPDATE_TAG": new_update_tag, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    stubber.assert_no_pending_responses()
    assert seeded
    assert check_nodes(neo4j_session, "AWSSecurityHub", ["id"]) == seeded
