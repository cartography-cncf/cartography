import copy
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ses
import tests.data.aws.ses
from cartography.intel.aws.ses import sync
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.ses,
    "get_ses_email_identities",
    return_value=copy.deepcopy(tests.data.aws.ses.GET_EMAIL_IDENTITIES),
)
def test_sync_ses_email_identities(mock_get_identities, neo4j_session):
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    neo4j_session.run("MATCH (n:SESEmailIdentity) DETACH DELETE n")

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(
        neo4j_session,
        "SESEmailIdentity",
        [
            "arn",
            "identity",
            "identity_type",
            "sending_enabled",
            "verification_status",
            "dkim_signing_enabled",
            "dkim_status",
            "region",
        ],
    ) == {
        (
            "arn:aws:ses:us-east-1:000000000000:identity/example.com",
            "example.com",
            "DOMAIN",
            True,
            "SUCCESS",
            True,
            "SUCCESS",
            "us-east-1",
        ),
        (
            "arn:aws:ses:us-east-1:000000000000:identity/user@example.com",
            "user@example.com",
            "EMAIL_ADDRESS",
            True,
            "SUCCESS",
            False,
            "NOT_STARTED",
            "us-east-1",
        ),
        (
            "arn:aws:ses:us-east-1:000000000000:identity/pending.io",
            "pending.io",
            "DOMAIN",
            False,
            "PENDING",
            False,
            "PENDING",
            "us-east-1",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "SESEmailIdentity",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:ses:us-east-1:000000000000:identity/example.com",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:ses:us-east-1:000000000000:identity/user@example.com",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:ses:us-east-1:000000000000:identity/pending.io",
        ),
    }


@patch.object(
    cartography.intel.aws.ses,
    "get_ses_email_identities",
    return_value=[],
)
def test_sync_ses_empty(mock_get_identities, neo4j_session):
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    neo4j_session.run("MATCH (n:SESEmailIdentity) DETACH DELETE n")

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert (
        check_nodes(
            neo4j_session,
            "SESEmailIdentity",
            ["arn"],
        )
        == set()
    )
