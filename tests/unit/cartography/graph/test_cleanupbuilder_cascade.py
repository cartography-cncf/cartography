"""Unit tests for cascade_delete feature in cleanup builder."""

from typing import List

from cartography.graph.cleanupbuilder import _build_cleanup_node_and_rel_queries
from cartography.graph.cleanupbuilder import build_cleanup_queries
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetSchema,
)
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetToSubResourceRel,
)
from tests.unit.cartography.graph.helpers import clean_query_list


def test_cascade_delete_false_generates_standard_delete():
    """
    Test that cascade_delete=False generates the standard DETACH DELETE n query.
    """
    actual_queries: List[str] = _build_cleanup_node_and_rel_queries(
        InterestingAssetSchema(),
        InterestingAssetToSubResourceRel(),
        cascade_delete=False,
    )
    # First query is the node cleanup, second is relationship cleanup
    node_cleanup_query = actual_queries[0]

    # Should have standard DETACH DELETE n without cascade
    assert "DETACH DELETE n;" in node_cleanup_query
    # Should NOT have OPTIONAL MATCH for children
    assert "OPTIONAL MATCH" not in node_cleanup_query
    assert "(child)" not in node_cleanup_query


def test_cascade_delete_true_generates_cascade_delete():
    """
    Test that cascade_delete=True generates a query that also deletes child nodes
    with RESOURCE relationships.
    """
    actual_queries: List[str] = _build_cleanup_node_and_rel_queries(
        InterestingAssetSchema(),
        InterestingAssetToSubResourceRel(),
        cascade_delete=True,
    )
    # First query is the node cleanup
    node_cleanup_query = actual_queries[0]

    # Should have OPTIONAL MATCH to find children with RESOURCE relationship
    # In Cartography, RESOURCE points from parent to child: (Parent)-[:RESOURCE]->(Child)
    assert "OPTIONAL MATCH (n)-[:RESOURCE]->(child)" in node_cleanup_query
    # Should delete both child and parent
    assert "DETACH DELETE child, n;" in node_cleanup_query


def test_cascade_delete_default_is_false():
    """
    Test that the default behavior (no cascade_delete argument) is cascade_delete=False.
    This ensures backward compatibility.
    """
    # Call without cascade_delete argument
    actual_queries: List[str] = _build_cleanup_node_and_rel_queries(
        InterestingAssetSchema(),
        InterestingAssetToSubResourceRel(),
    )
    node_cleanup_query = actual_queries[0]

    # Default should be no cascade - standard delete
    assert "DETACH DELETE n;" in node_cleanup_query
    assert "OPTIONAL MATCH" not in node_cleanup_query


def test_build_cleanup_queries_cascade_delete_true():
    """
    Test that build_cleanup_queries with cascade_delete=True generates the full set
    of cleanup queries with cascade delete for the node cleanup.
    """
    actual_queries: list[str] = build_cleanup_queries(
        InterestingAssetSchema(),
        cascade_delete=True,
    )

    # First query should be node cleanup with cascade
    node_cleanup_query = actual_queries[0]
    assert "OPTIONAL MATCH (n)-[:RESOURCE]->(child)" in node_cleanup_query
    assert "DETACH DELETE child, n;" in node_cleanup_query


def test_build_cleanup_queries_cascade_delete_false():
    """
    Test that build_cleanup_queries with cascade_delete=False generates standard queries.
    """
    actual_queries: list[str] = build_cleanup_queries(
        InterestingAssetSchema(),
        cascade_delete=False,
    )

    # First query should be standard node cleanup without cascade
    node_cleanup_query = actual_queries[0]
    assert "DETACH DELETE n;" in node_cleanup_query
    assert "OPTIONAL MATCH" not in node_cleanup_query


def test_cascade_delete_full_query_structure():
    """
    Test the complete structure of the generated cascade delete query.
    """
    actual_queries: List[str] = _build_cleanup_node_and_rel_queries(
        InterestingAssetSchema(),
        InterestingAssetToSubResourceRel(),
        cascade_delete=True,
    )

    expected_node_cleanup = """
        MATCH (n:InterestingAsset)<-[s:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        OPTIONAL MATCH (n)-[:RESOURCE]->(child)
        DETACH DELETE child, n;
    """

    expected_rel_cleanup = """
        MATCH (n:InterestingAsset)<-[s:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        WHERE s.lastupdated <> $UPDATE_TAG
        WITH s LIMIT $LIMIT_SIZE
        DELETE s;
    """

    assert clean_query_list(actual_queries) == clean_query_list(
        [expected_node_cleanup, expected_rel_cleanup]
    )


def test_cascade_delete_false_full_query_structure():
    """
    Test the complete structure of the generated standard (non-cascade) delete query.
    """
    actual_queries: List[str] = _build_cleanup_node_and_rel_queries(
        InterestingAssetSchema(),
        InterestingAssetToSubResourceRel(),
        cascade_delete=False,
    )

    expected_node_cleanup = """
        MATCH (n:InterestingAsset)<-[s:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
    """

    expected_rel_cleanup = """
        MATCH (n:InterestingAsset)<-[s:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        WHERE s.lastupdated <> $UPDATE_TAG
        WITH s LIMIT $LIMIT_SIZE
        DELETE s;
    """

    assert clean_query_list(actual_queries) == clean_query_list(
        [expected_node_cleanup, expected_rel_cleanup]
    )
