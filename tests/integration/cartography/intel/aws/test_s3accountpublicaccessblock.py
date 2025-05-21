from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.s3accountpublicaccessblock
import tests.data.aws.s3accountpublicaccessblock
from cartography.intel.aws.s3accountpublicaccessblock import sync
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.s3accountpublicaccessblock,
    "get_account_public_access_block",
    return_value=[tests.data.aws.s3accountpublicaccessblock.GET_PUBLIC_ACCESS_BLOCK],
)
def test_sync_s3accountpublicaccessblock(mock_get_pab, neo4j_session):
    """
    Test that S3 Account Public Access Block settings are correctly synced to the graph.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    neo4j_session.run("MATCH (n:S3AccountPublicAccessBlock) DETACH DELETE n")

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
        "S3AccountPublicAccessBlock",
        [
            "id",
            "block_public_acls",
            "ignore_public_acls",
            "block_public_policy",
            "restrict_public_buckets",
        ],
    ) == {
        (
            f"{TEST_ACCOUNT_ID}:{TEST_REGION}",
            True,
            True,
            True,
            True,
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "S3AccountPublicAccessBlock",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, f"{TEST_ACCOUNT_ID}:{TEST_REGION}"),
    }


@patch.object(
    cartography.intel.aws.s3accountpublicaccessblock,
    "get_account_public_access_block",
    return_value=[],
)
def test_sync_s3accountpublicaccessblock_none(mock_get_pab, neo4j_session):
    """
    Test that when no S3 Account Public Access Block settings exist, no nodes are created.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    neo4j_session.run("MATCH (n:S3AccountPublicAccessBlock) DETACH DELETE n")

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    nodes = neo4j_session.run(
        """
        MATCH (n:S3AccountPublicAccessBlock) RETURN n.id;
        """
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == set()


@patch.object(
    cartography.intel.aws.s3accountpublicaccessblock,
    "get_account_public_access_block",
    return_value=[
        tests.data.aws.s3accountpublicaccessblock.GET_PUBLIC_ACCESS_BLOCK_PARTIAL
    ],
)
def test_sync_s3accountpublicaccessblock_partial(mock_get_pab, neo4j_session):
    """
    Test that S3 Account Public Access Block settings with some settings disabled are correctly synced.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    neo4j_session.run("MATCH (n:S3AccountPublicAccessBlock) DETACH DELETE n")

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
        "S3AccountPublicAccessBlock",
        [
            "id",
            "block_public_acls",
            "ignore_public_acls",
            "block_public_policy",
            "restrict_public_buckets",
        ],
    ) == {
        (
            f"{TEST_ACCOUNT_ID}:{TEST_REGION}",
            True,
            False,
            True,
            False,
        ),
    }
