"""
Unit tests for Cartography matchlink functionality.

Tests the query building functions for matchlink operations.
"""

from dataclasses import dataclass
from unittest.mock import patch

import pytest

from cartography.graph.cleanupbuilder import build_cleanup_query_for_matchlink
from cartography.graph.querybuilder import build_create_index_queries_for_matchlink
from cartography.graph.querybuilder import build_matchlink_cartesian_product_query
from cartography.graph.querybuilder import build_matchlink_query
from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import MatchLinkSubResource
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from tests.data.graph.matchlink.iam_permissions import (
    PrincipalToS3BucketCartesianProductInwardPermissionRel,
)
from tests.data.graph.matchlink.iam_permissions import (
    PrincipalToS3BucketCartesianProductPermissionRel,
)
from tests.data.graph.matchlink.iam_permissions import PrincipalToS3BucketPermissionRel
from tests.data.graph.matchlink.iam_permissions import (
    PrincipalToS3BucketScopedPermissionRel,
)
from tests.data.graph.matchlink.iam_permissions import (
    PrincipalToS3BucketSourceScopedPermissionRel,
)
from tests.data.graph.matchlink.iam_permissions import (
    PrincipalToS3BucketTargetScopedOutwardPermissionRel,
)
from tests.data.graph.matchlink.iam_permissions import (
    PrincipalToS3BucketTargetScopedPermissionRel,
)
from tests.data.graph.matchlink.iam_permissions import (
    PrincipalToS3BucketUnequalScopedPermissionRel,
)
from tests.unit.cartography.graph.helpers import (
    remove_leading_whitespace_and_empty_lines,
)


@dataclass(frozen=True)
class PrincipalToS3BucketCartesianProductMultiSourceMatcherRel(
    PrincipalToS3BucketCartesianProductPermissionRel
):
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "principal_arn": PropertyRef("principal_arn"),
            "account_id": PropertyRef("account_id"),
        }
    )


@dataclass(frozen=True)
class PrincipalToS3BucketCartesianProductOneToManyTargetMatcherRel(
    PrincipalToS3BucketCartesianProductPermissionRel
):
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("BucketNames", one_to_many=True),
        }
    )


@dataclass(frozen=True)
class PrincipalToS3BucketCartesianProductIgnoreCaseTargetMatcherRel(
    PrincipalToS3BucketCartesianProductPermissionRel
):
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("BucketName", ignore_case=True),
        }
    )


@dataclass(frozen=True)
class PrincipalToS3BucketCartesianProductFuzzyTargetMatcherRel(
    PrincipalToS3BucketCartesianProductPermissionRel
):
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("BucketName", fuzzy_and_ignore_case=True),
        }
    )


@dataclass(frozen=True)
class PrincipalToS3BucketCartesianProductSourceScopedRel(
    PrincipalToS3BucketCartesianProductPermissionRel
):
    source_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="AWSAccount",
        target_node_matcher=make_target_node_matcher(
            {"id": PropertyRef("_sub_resource_id", set_in_kwargs=True)},
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )


@patch("cartography.graph.querybuilder.get_cartography_version", return_value="3.14.16")
def test_build_matchlink_query(_mock_get_cartography_version):
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


@patch("cartography.graph.querybuilder.get_cartography_version", return_value="3.14.16")
def test_build_matchlink_cartesian_product_query(_mock_get_cartography_version):
    # Arrange
    rel_schema = PrincipalToS3BucketCartesianProductPermissionRel()

    # Act
    link_query = build_matchlink_cartesian_product_query(rel_schema)

    # Assert
    expected = """
        UNWIND $SourceValues AS source_value
            MATCH (from:AWSPrincipal{principal_arn: source_value})
        WITH collect(from) AS sources
        UNWIND $TargetValues AS target_value
            MATCH (to:S3Bucket{name: target_value})
        WITH sources, to
        UNWIND sources AS from
            MERGE (from)-[r:CAN_BULK_ACCESS]->(to)
            ON CREATE SET r.firstseen = timestamp()
            SET
                r._module_name = "unknown:tests.data.graph.matchlink.iam_permissions",
                r._module_version = "3.14.16",
                r.lastupdated = $UPDATE_TAG,
                r._sub_resource_label = $_sub_resource_label,
                r._sub_resource_id = $_sub_resource_id
        RETURN count(r) AS rel_count;
    """
    actual_query = remove_leading_whitespace_and_empty_lines(link_query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query


@patch("cartography.graph.querybuilder.get_cartography_version", return_value="3.14.16")
def test_build_matchlink_cartesian_product_query_inward_direction(
    _mock_get_cartography_version,
):
    # Arrange
    rel_schema = PrincipalToS3BucketCartesianProductInwardPermissionRel()

    # Act
    link_query = build_matchlink_cartesian_product_query(rel_schema)

    # Assert
    assert "MERGE (from)<-[r:CAN_BULK_ACCESS]-(to)" in link_query
    assert "RETURN count(r) AS rel_count" in link_query


def test_build_matchlink_cartesian_product_query_rejects_multiple_matcher_keys():
    # Arrange
    rel_schema = PrincipalToS3BucketCartesianProductMultiSourceMatcherRel()

    # Act and assert
    with pytest.raises(ValueError, match="exactly one source matcher key"):
        build_matchlink_cartesian_product_query(rel_schema)


def test_build_matchlink_cartesian_product_query_rejects_one_to_many_matcher():
    # Arrange
    rel_schema = PrincipalToS3BucketCartesianProductOneToManyTargetMatcherRel()

    # Act and assert
    with pytest.raises(ValueError, match="one_to_many"):
        build_matchlink_cartesian_product_query(rel_schema)


def test_build_matchlink_cartesian_product_query_rejects_ignore_case_matcher():
    # Arrange
    rel_schema = PrincipalToS3BucketCartesianProductIgnoreCaseTargetMatcherRel()

    # Act and assert
    with pytest.raises(ValueError, match="ignore_case"):
        build_matchlink_cartesian_product_query(rel_schema)


def test_build_matchlink_cartesian_product_query_rejects_fuzzy_matcher():
    # Arrange
    rel_schema = PrincipalToS3BucketCartesianProductFuzzyTargetMatcherRel()

    # Act and assert
    with pytest.raises(ValueError, match="fuzzy_and_ignore_case"):
        build_matchlink_cartesian_product_query(rel_schema)


def test_build_matchlink_cartesian_product_query_rejects_endpoint_sub_resource():
    # Arrange
    rel_schema = PrincipalToS3BucketCartesianProductSourceScopedRel()

    # Act and assert
    with pytest.raises(ValueError, match="endpoint sub-resource"):
        build_matchlink_cartesian_product_query(rel_schema)


def test_build_matchlink_cartesian_product_query_rejects_row_relationship_properties():
    # Arrange
    rel_schema = PrincipalToS3BucketPermissionRel()

    # Act and assert
    with pytest.raises(ValueError, match="relationship properties set from kwargs"):
        build_matchlink_cartesian_product_query(rel_schema)


@patch("cartography.graph.querybuilder.get_cartography_version", return_value="3.14.16")
def test_build_source_scoped_matchlink_query(_mock_get_cartography_version):
    rel_schema = PrincipalToS3BucketSourceScopedPermissionRel()
    link_query = build_matchlink_query(rel_schema)

    expected = """
        MATCH (source_sub_resource:AWSAccount{id: $_sub_resource_id})
        UNWIND $DictList as item
            MATCH (from:AWSPrincipal{principal_arn: item.principal_arn})<-[:RESOURCE]-(source_sub_resource)
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

    actual_query = remove_leading_whitespace_and_empty_lines(link_query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query


@patch("cartography.graph.querybuilder.get_cartography_version", return_value="3.14.16")
def test_build_target_scoped_matchlink_query(_mock_get_cartography_version):
    rel_schema = PrincipalToS3BucketTargetScopedPermissionRel()
    link_query = build_matchlink_query(rel_schema)

    expected = """
        MATCH (target_sub_resource:AWSAccount{id: $_sub_resource_id})
        UNWIND $DictList as item
            MATCH (from:AWSPrincipal{principal_arn: item.principal_arn})
            MATCH (to:S3Bucket{name: item.BucketName})<-[:RESOURCE]-(target_sub_resource)
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

    actual_query = remove_leading_whitespace_and_empty_lines(link_query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query


@patch("cartography.graph.querybuilder.get_cartography_version", return_value="3.14.16")
def test_build_scoped_matchlink_query(_mock_get_cartography_version):
    rel_schema = PrincipalToS3BucketScopedPermissionRel()
    link_query = build_matchlink_query(rel_schema)

    expected = """
        MATCH (sub_resource:AWSAccount{id: $_sub_resource_id})
        UNWIND $DictList as item
            MATCH (from:AWSPrincipal{principal_arn: item.principal_arn})<-[:RESOURCE]-(sub_resource)
            MATCH (to:S3Bucket{name: item.BucketName})<-[:RESOURCE]-(sub_resource)
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

    actual_query = remove_leading_whitespace_and_empty_lines(link_query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query


@patch("cartography.graph.querybuilder.get_cartography_version", return_value="3.14.16")
def test_build_unequal_scoped_matchlink_query(_mock_get_cartography_version):
    rel_schema = PrincipalToS3BucketUnequalScopedPermissionRel()
    link_query = build_matchlink_query(rel_schema)

    expected = """
        MATCH (source_sub_resource:AWSAccount{id: $_sub_resource_id})
        MATCH (target_sub_resource:AWSOrganization{id: $_sub_resource_id})
        UNWIND $DictList as item
            MATCH (from:AWSPrincipal{principal_arn: item.principal_arn})<-[:RESOURCE]-(source_sub_resource)
            MATCH (to:S3Bucket{name: item.BucketName})<-[:RESOURCE]-(target_sub_resource)
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

    actual_query = remove_leading_whitespace_and_empty_lines(link_query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query


@patch("cartography.graph.querybuilder.get_cartography_version", return_value="3.14.16")
def test_build_outward_scoped_matchlink_query(_mock_get_cartography_version):
    rel_schema = PrincipalToS3BucketTargetScopedOutwardPermissionRel()
    link_query = build_matchlink_query(rel_schema)

    expected = """
        MATCH (target_sub_resource:AWSAccount{id: $_sub_resource_id})
        UNWIND $DictList as item
            MATCH (from:AWSPrincipal{principal_arn: item.principal_arn})
            MATCH (to:S3Bucket{name: item.BucketName})-[:RESOURCE]->(target_sub_resource)
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
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:CAN_ACCESS]->() ON (r._sub_resource_label, r._sub_resource_id, r.lastupdated);",
    }

    # Assert: compare the list of index queries
    assert set(index_queries) == expected_queries


def test_build_create_index_queries_for_scoped_matchlink():
    rel_schema = PrincipalToS3BucketScopedPermissionRel()
    index_queries = build_create_index_queries_for_matchlink(rel_schema)

    expected_queries = {
        "CREATE INDEX IF NOT EXISTS FOR (n:AWSPrincipal) ON (n.principal_arn);",
        "CREATE INDEX IF NOT EXISTS FOR (n:S3Bucket) ON (n.name);",
        "CREATE INDEX IF NOT EXISTS FOR (n:AWSAccount) ON (n.id);",
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:CAN_ACCESS]->() ON (r._sub_resource_label, r._sub_resource_id, r.lastupdated);",
    }

    assert set(index_queries) == expected_queries
