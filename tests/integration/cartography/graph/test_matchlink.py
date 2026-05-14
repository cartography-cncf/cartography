"""
Integration tests for Cartography matchlink functionality.

Tests the load_matchlinks() function and cleanup operations for relationship schemas.
"""

import neo4j
import pytest

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from tests.data.graph.matchlink.iam_permissions import PrincipalToS3BucketPermissionRel
from tests.data.graph.matchlink.iam_permissions import (
    PrincipalToS3BucketScopedPermissionRel,
)
from tests.integration.util import check_rels

# Test data constants
TEST_UPDATE_TAG_1 = 1111
TEST_UPDATE_TAG_2 = 2222
TEST_ACCOUNT_1 = "9876"
TEST_ACCOUNT_2 = "1234"
TEST_SCOPED_ACCOUNT_1 = "scoped-account-1"
TEST_SCOPED_ACCOUNT_2 = "scoped-account-2"


def _setup_test_data(neo4j_session: neo4j.Session, update_tag: int) -> None:
    """
    Set up test data in Neo4j for the integration test.

    Creates:
    - Account 9876 with principals p1, p2 and buckets b1, b2, b3
    - Account 1234 with principal p3 and bucket b4
    """
    # Account 9876 has principals p1 and p2, and buckets b1, b2, b3
    neo4j_session.run(
        """
        MERGE (acc:AWSAccount {id: $account_id, lastupdated: $update_tag})
        MERGE (p1:AWSPrincipal {principal_arn: $p1_arn, lastupdated: $update_tag})
        MERGE (acc)-[res1:RESOURCE]->(p1)

        MERGE (p2:AWSPrincipal {principal_arn: $p2_arn, lastupdated: $update_tag})
        MERGE (acc)-[res2:RESOURCE]->(p2)

        MERGE (b1:S3Bucket {name: $b1_name, lastupdated: $update_tag})
        MERGE (acc)-[res3:RESOURCE]->(b1)

        MERGE (b2:S3Bucket {name: $b2_name, lastupdated: $update_tag})
        MERGE (acc)-[res4:RESOURCE]->(b2)

        MERGE (b3:S3Bucket {name: $b3_name, lastupdated: $update_tag})
        MERGE (acc)-[res5:RESOURCE]->(b3)
        SET res1.lastupdated = $update_tag, res2.lastupdated = $update_tag,
            res3.lastupdated = $update_tag, res4.lastupdated = $update_tag, res5.lastupdated = $update_tag
        """,
        {
            "account_id": TEST_ACCOUNT_1,
            "p1_arn": "arn:aws:iam::9876:role/Admin",
            "p2_arn": "arn:aws:iam::9876:role/Viewer",
            "b1_name": "sensitive-data",
            "b2_name": "public-bucket",
            "b3_name": "private-bucket",
            "update_tag": update_tag,
        },
    )

    # Account 1234 has principal p3, and bucket b4
    neo4j_session.run(
        """
        MERGE (acc2:AWSAccount {id: $account_id, lastupdated: $update_tag})
        MERGE (p3:AWSPrincipal {principal_arn: $p3_arn, lastupdated: $update_tag})
        MERGE (acc2)-[res5:RESOURCE]->(p3)

        MERGE (b4:S3Bucket {name: $b4_name, lastupdated: $update_tag})
        MERGE (acc2)-[res6:RESOURCE]->(b4)
        SET res5.lastupdated = $update_tag, res6.lastupdated = $update_tag
        """,
        {
            "account_id": TEST_ACCOUNT_2,
            "p3_arn": "arn:aws:iam::1234:role/Admin",
            "b4_name": "www-bucket",
            "update_tag": update_tag,
        },
    )


def _setup_duplicate_matchlink_test_data(
    neo4j_session: neo4j.Session, update_tag: int
) -> None:
    """
    Set up duplicate source and target matcher values across two accounts.

    The duplicate properties intentionally model the case where a MatchLink's
    endpoint matcher is only unique inside its sub-resource.
    """
    neo4j_session.run(
        """
        CREATE (acc1:AWSAccount {id: $account_1, lastupdated: $update_tag})
        CREATE (p1:AWSPrincipal {principal_arn: $principal_arn, lastupdated: $update_tag})
        CREATE (b1:S3Bucket {name: $bucket_name, lastupdated: $update_tag})
        CREATE (acc1)-[:RESOURCE {lastupdated: $update_tag}]->(p1)
        CREATE (acc1)-[:RESOURCE {lastupdated: $update_tag}]->(b1)

        CREATE (acc2:AWSAccount {id: $account_2, lastupdated: $update_tag})
        CREATE (p2:AWSPrincipal {principal_arn: $principal_arn, lastupdated: $update_tag})
        CREATE (b2:S3Bucket {name: $bucket_name, lastupdated: $update_tag})
        CREATE (acc2)-[:RESOURCE {lastupdated: $update_tag}]->(p2)
        CREATE (acc2)-[:RESOURCE {lastupdated: $update_tag}]->(b2)
        """,
        {
            "account_1": TEST_SCOPED_ACCOUNT_1,
            "account_2": TEST_SCOPED_ACCOUNT_2,
            "principal_arn": "shared-principal",
            "bucket_name": "shared-bucket",
            "update_tag": update_tag,
        },
    )


def test_load_rels_and_cleanup_integration(neo4j_session):
    """
    Integration test for load_rels() function and cleanup operations.

    Tests the complete flow:
    1. Set up test data (accounts, principals, buckets)
    2. Load relationships for account 1 at time t1
    3. Load relationships for account 2 at time t1
    4. Load relationships for account 1 at time t2 (different permissions)
    5. Verify that account 2 relationships remain unchanged
    """
    matchlink = PrincipalToS3BucketPermissionRel()

    # Arrange: Set up initial test data
    _setup_test_data(neo4j_session, TEST_UPDATE_TAG_1)

    # Act: in account 1, p1 can access b1, and p2 can access b2. Nothing can access b3.
    mapping_data_acc1_t1 = [
        {
            "principal_arn": "arn:aws:iam::9876:role/Admin",
            "BucketName": "sensitive-data",
            "permission_action": "s3:GetObject",
        },
        {
            "principal_arn": "arn:aws:iam::9876:role/Viewer",
            "BucketName": "public-bucket",
            "permission_action": "s3:ListBucket",
        },
    ]
    common_job_parameters_acc1_t1 = {
        "UPDATE_TAG": TEST_UPDATE_TAG_1,
        "_sub_resource_label": "AWSAccount",
        "_sub_resource_id": TEST_ACCOUNT_1,
    }
    load_matchlinks(
        neo4j_session, matchlink, mapping_data_acc1_t1, **common_job_parameters_acc1_t1
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSPrincipal",
        "principal_arn",
        "S3Bucket",
        "name",
        "CAN_ACCESS",
        rel_direction_right=True,
    ) == {
        # Account 1
        ("arn:aws:iam::9876:role/Admin", "sensitive-data"),
        ("arn:aws:iam::9876:role/Viewer", "public-bucket"),
    }

    # Act: in account 2, p3 can access b4
    mapping_data_acc2_t1 = [
        {
            "principal_arn": "arn:aws:iam::1234:role/Admin",
            "BucketName": "www-bucket",
            "permission_action": "s3:GetObject",
        }
    ]
    common_job_parameters_acc2_t1 = {
        "UPDATE_TAG": TEST_UPDATE_TAG_1,
        "_sub_resource_label": "AWSAccount",
        "_sub_resource_id": TEST_ACCOUNT_2,
    }
    load_matchlinks(
        neo4j_session, matchlink, mapping_data_acc2_t1, **common_job_parameters_acc2_t1
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSPrincipal",
        "principal_arn",
        "S3Bucket",
        "name",
        "CAN_ACCESS",
        rel_direction_right=True,
    ) == {
        # Account 1
        ("arn:aws:iam::9876:role/Admin", "sensitive-data"),
        ("arn:aws:iam::9876:role/Viewer", "public-bucket"),
        # Account 2
        ("arn:aws:iam::1234:role/Admin", "www-bucket"),
    }

    # Act: in account 1, p1 can access b1 and b3. p2 cannot access any buckets. Nothing can access b2.
    mapping_data_acc1_t2 = [
        {
            "principal_arn": "arn:aws:iam::9876:role/Admin",
            "BucketName": "sensitive-data",
            "permission_action": "s3:GetObject",
        },
        {
            "principal_arn": "arn:aws:iam::9876:role/Admin",
            "BucketName": "private-bucket",
            "permission_action": "s3:GetObject",
        },
    ]
    common_job_parameters_acc1_t2 = {
        "UPDATE_TAG": TEST_UPDATE_TAG_2,
        "_sub_resource_label": "AWSAccount",
        "_sub_resource_id": TEST_ACCOUNT_1,
    }
    load_matchlinks(
        neo4j_session, matchlink, mapping_data_acc1_t2, **common_job_parameters_acc1_t2
    )

    # Act: Run cleanup for account 1 at t2
    cleanup_job = GraphJob.from_matchlink(
        matchlink, "AWSAccount", TEST_ACCOUNT_1, TEST_UPDATE_TAG_2
    )
    cleanup_job.run(neo4j_session)

    # Assert: Account 1 should only have the new relationships from t2, and account 2 should still have its relationships (unchanged)
    assert check_rels(
        neo4j_session,
        "AWSPrincipal",
        "principal_arn",
        "S3Bucket",
        "name",
        "CAN_ACCESS",
        rel_direction_right=True,
    ) == {
        # Account 1 at time t2
        ("arn:aws:iam::9876:role/Admin", "sensitive-data"),
        ("arn:aws:iam::9876:role/Admin", "private-bucket"),
        # Account 2 is still at time t1 but it hasn't been updated so we don't delete anything in there
        ("arn:aws:iam::1234:role/Admin", "www-bucket"),
    }

    # Assert: assets in account 2 are still at time t1
    result = neo4j_session.run(
        """
        MATCH (:AWSAccount {id: $account_id})-[r:RESOURCE]->()
        RETURN DISTINCT r.lastupdated as lastupdated
    """,
        {"account_id": TEST_ACCOUNT_2},
    )
    lastupdated_list = [row["lastupdated"] for row in result]
    assert (
        len(lastupdated_list) == 1
    ), f"There should be just one timestamp across all relationships in account {TEST_ACCOUNT_2}"
    assert lastupdated_list[0] == TEST_UPDATE_TAG_1, (
        f"Data isolation test failed: Account {TEST_ACCOUNT_2} relationships "
        f"should be set to timestamp {TEST_UPDATE_TAG_1}"
    )


def test_scoped_matchlinks_do_not_cross_sub_resources(neo4j_session):
    matchlink = PrincipalToS3BucketScopedPermissionRel()
    _setup_duplicate_matchlink_test_data(neo4j_session, TEST_UPDATE_TAG_1)

    load_matchlinks(
        neo4j_session,
        matchlink,
        [
            {
                "principal_arn": "shared-principal",
                "BucketName": "shared-bucket",
                "permission_action": "s3:GetObject",
            },
        ],
        UPDATE_TAG=TEST_UPDATE_TAG_1,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=TEST_SCOPED_ACCOUNT_1,
    )

    scoped_counts = neo4j_session.run(
        """
        MATCH (account:AWSAccount)-[:RESOURCE]->(principal:AWSPrincipal)
        WHERE account.id IN $account_ids
        MATCH (account)-[:RESOURCE]->(bucket:S3Bucket)
        OPTIONAL MATCH (principal)-[r:CAN_ACCESS]->(bucket)
        RETURN account.id AS account_id, count(r) AS rel_count
        ORDER BY account_id
        """,
        {"account_ids": [TEST_SCOPED_ACCOUNT_1, TEST_SCOPED_ACCOUNT_2]},
    )

    assert [(row["account_id"], row["rel_count"]) for row in scoped_counts] == [
        (TEST_SCOPED_ACCOUNT_1, 1),
        (TEST_SCOPED_ACCOUNT_2, 0),
    ]

    cross_scope_count = neo4j_session.run(
        """
        MATCH (source_account:AWSAccount)-[:RESOURCE]->(principal:AWSPrincipal)
        MATCH (target_account:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
        MATCH (principal)-[r:CAN_ACCESS]->(bucket)
        WHERE source_account.id IN $account_ids
            AND target_account.id IN $account_ids
            AND source_account.id <> target_account.id
        RETURN count(r) AS rel_count
        """,
        {"account_ids": [TEST_SCOPED_ACCOUNT_1, TEST_SCOPED_ACCOUNT_2]},
    ).single()["rel_count"]
    assert cross_scope_count == 0


def test_load_rels_missing_kwargs(neo4j_session):
    """
    Test that load_rels() raises appropriate errors when required kwargs are missing.
    """
    rel_schema = PrincipalToS3BucketPermissionRel()

    # Test missing _sub_resource_label - need non-empty list to avoid early return
    with pytest.raises(
        ValueError, match="Required kwarg '_sub_resource_label' not provided"
    ):
        load_matchlinks(
            neo4j_session, rel_schema, [{"test": "data"}], _sub_resource_id="test"
        )

    # Test missing _sub_resource_id - need non-empty list to avoid early return
    with pytest.raises(
        ValueError, match="Required kwarg '_sub_resource_id' not provided"
    ):
        load_matchlinks(
            neo4j_session, rel_schema, [{"test": "data"}], _sub_resource_label="test"
        )

    # Test missing both kwargs - should fail on first check (_sub_resource_label)
    with pytest.raises(
        ValueError, match="Required kwarg '_sub_resource_label' not provided"
    ):
        load_matchlinks(neo4j_session, rel_schema, [{"test": "data"}])
