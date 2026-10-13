from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.aws.s3accountpublicaccessblock
import tests.data.aws.s3accountpublicaccessblock
from cartography.intel.aws.s3accountpublicaccessblock import sync
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@pytest.mark.parametrize(
    "api_return,expected_nodes,expected_rels",
    [
        (
            [tests.data.aws.s3accountpublicaccessblock.GET_PUBLIC_ACCESS_BLOCK],
            {
                (
                    f"{TEST_ACCOUNT_ID}:{TEST_REGION}",
                    True,
                    True,
                    True,
                    True,
                ),
            },
            {(TEST_ACCOUNT_ID, f"{TEST_ACCOUNT_ID}:{TEST_REGION}")},
        ),
        (
            [],
            set(),
            set(),
        ),
        (
            [tests.data.aws.s3accountpublicaccessblock.GET_PUBLIC_ACCESS_BLOCK_PARTIAL],
            {
                (
                    f"{TEST_ACCOUNT_ID}:{TEST_REGION}",
                    True,
                    False,
                    True,
                    False,
                ),
            },
            {(TEST_ACCOUNT_ID, f"{TEST_ACCOUNT_ID}:{TEST_REGION}")},
        ),
    ],
    ids=["full", "none", "partial"],
)
def test_sync_s3accountpublicaccessblock(
    neo4j_session, api_return, expected_nodes, expected_rels
):
    """
    Test that S3 Account Public Access Block settings are correctly synced to the
    graph: fully enabled, absent (no nodes created), and partially enabled.
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    neo4j_session.run("MATCH (n:AWSS3AccountPublicAccessBlock) DETACH DELETE n")

    # Act
    with patch.object(
        cartography.intel.aws.s3accountpublicaccessblock,
        "get_account_public_access_block",
        return_value=api_return,
    ):
        sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        )

    # Assert
    assert (
        check_nodes(
            neo4j_session,
            "AWSS3AccountPublicAccessBlock",
            [
                "id",
                "block_public_acls",
                "ignore_public_acls",
                "block_public_policy",
                "restrict_public_buckets",
            ],
        )
        == expected_nodes
    )

    assert (
        check_rels(
            neo4j_session,
            "AWSAccount",
            "id",
            "AWSS3AccountPublicAccessBlock",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_rels
    )
