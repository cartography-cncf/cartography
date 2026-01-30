"""
Unit tests for Cartography matchlink functionality.

Tests the query building functions for matchlink operations.
"""

from unittest.mock import patch

from cartography.graph.cleanupbuilder import build_cleanup_query_for_matchlink
from cartography.graph.querybuilder import build_create_index_queries_for_matchlink
from cartography.graph.querybuilder import build_matchlink_query
from tests.data.graph.matchlink.iam_permissions import PrincipalToS3BucketPermissionRel
from tests.unit.cartography.graph.helpers import (
    remove_leading_whitespace_and_empty_lines,
)


@patch(
    "cartography.graph.querybuilder._get_cartography_version", return_value="3.14.16"
)
def test_build_matchlink_query(mock_get_cartography_version):
    """
    Test that build_matchlink_query() generates valid Cypher queries.
    """
    rel_schema = PrincipalToS3BucketPermissionRel()
    link_query = build_matchlink_query(rel_schema)

    expected = """
        UNWIND $DictList as item
            MATCH (from:AWSPrincipal{principal_arn: item.principal_arn})
            MATCH (to:S3Bucket{name: item.BucketName})
            MERGE (from)-[r:CAN_ACCESS]->(to)
            ON CREATE SET r.firstseen = timestamp()
            SET
                r._module_name = "unknown:tests.data.graph.matchlink.iam_permissions",
                r._module_version = "3.14.16",
                r.lastupdated = $UPDATE_TAG,
                r.permission_action = item.permission_action,
                r._sub_resource_label = $_sub_resource_label,
                r._sub_resource_id = $_sub_resource_id;
    """

    # Assert: compare query outputs while ignoring leading whitespace.
    actual_query = remove_leading_whitespace_and_empty_lines(link_query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query


def test_build_cleanup_query_for_matchlink():
    """
    Test that build_cleanup_query_for_matchlink() generates valid cleanup queries.
    """
    rel_schema = PrincipalToS3BucketPermissionRel()
    cleanup_query = build_cleanup_query_for_matchlink(rel_schema)

    expected = """
        MATCH (from:AWSPrincipal)-[r:CAN_ACCESS]->(to:S3Bucket)
        WHERE r.lastupdated <> $UPDATE_TAG
            AND r._sub_resource_label = $_sub_resource_label
            AND r._sub_resource_id = $_sub_resource_id
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
    """

    # Assert: compare query outputs while ignoring leading whitespace.
    actual_query = remove_leading_whitespace_and_empty_lines(cleanup_query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query


def test_build_create_index_queries_for_matchlink():
    """
    Test that build_create_index_queries_for_matchlink() generates valid index creation queries.
    """
    rel_schema = PrincipalToS3BucketPermissionRel()
    index_queries = build_create_index_queries_for_matchlink(rel_schema)

    expected_queries = {
        "CREATE INDEX IF NOT EXISTS FOR (n:AWSPrincipal) ON (n.principal_arn);",
        "CREATE INDEX IF NOT EXISTS FOR (n:S3Bucket) ON (n.name);",
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:CAN_ACCESS]->() ON (r.lastupdated, r._sub_resource_label, r._sub_resource_id);",
    }

    # Assert: compare the list of index queries
    assert set(index_queries) == expected_queries
