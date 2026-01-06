"""
Integration tests for cascade_delete cleanup feature.

Tests the core behavior: when cascade_delete=True, deleting a stale parent
also deletes its children (nodes with relationships from the parent matching the
sub_resource_relationship rel_label).
"""

from cartography.client.core.tx import load_graph_data
from cartography.graph.job import GraphJob
from cartography.graph.querybuilder import build_ingestion_query
from tests.data.graph.querybuilder.sample_data.helloworld_relationships import (
    INTERESTING_NODE_WITH_ALL_RELS,
)
from tests.data.graph.querybuilder.sample_data.helloworld_relationships import (
    MERGE_HELLO_ASSET_QUERY,
)
from tests.data.graph.querybuilder.sample_data.helloworld_relationships import (
    MERGE_SUB_RESOURCE_QUERY,
)
from tests.data.graph.querybuilder.sample_data.helloworld_relationships import (
    MERGE_WORLD_ASSET_QUERY,
)
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetSchema,
)
from tests.integration.util import check_nodes


def _setup_parent_with_children(neo4j_session, lastupdated: int):
    """Create an InterestingAsset parent with two child nodes connected via sub_resource rel label."""
    neo4j_session.run(MERGE_SUB_RESOURCE_QUERY)
    neo4j_session.run(MERGE_HELLO_ASSET_QUERY)
    neo4j_session.run(MERGE_WORLD_ASSET_QUERY)

    query = build_ingestion_query(InterestingAssetSchema())
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_WITH_ALL_RELS,
        lastupdated=lastupdated,
        sub_resource_id="sub-resource-id",
    )

    # Create children with sub_resource relationship label toward parent: (Child)-[:RELATIONSHIP_LABEL]->(Parent)
    neo4j_session.run(
        """
        UNWIND ['child-1', 'child-2'] AS child_id
        MERGE (c:ChildNode{id: child_id})
        SET c.lastupdated = $lastupdated
        WITH c
        MATCH (p:InterestingAsset{id: 'interesting-node-id'})
        MERGE (c)-[:RELATIONSHIP_LABEL]->(p)
        """,
        lastupdated=lastupdated,
    )


def test_cascade_delete_removes_children_of_stale_parent(neo4j_session):
    """
    Test cascade_delete=True: when parent is stale, both parent AND children are deleted.
    """
    _setup_parent_with_children(neo4j_session, lastupdated=1)

    # Cleanup with UPDATE_TAG=2 makes parent stale; cascade should delete children too
    GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "sub-resource-id"},
        cascade_delete=True,
    ).run(neo4j_session)

    assert check_nodes(neo4j_session, "InterestingAsset", ["id"]) == set()
    assert check_nodes(neo4j_session, "ChildNode", ["id"]) == set()


def test_default_no_cascade_preserves_children(neo4j_session):
    """
    Test backwards compatibility: default (no cascade) leaves children orphaned.
    """
    _setup_parent_with_children(neo4j_session, lastupdated=1)

    # Cleanup without cascade_delete - should default to False
    GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "sub-resource-id"},
    ).run(neo4j_session)

    # Parent deleted, children remain orphaned
    assert check_nodes(neo4j_session, "InterestingAsset", ["id"]) == set()
    assert check_nodes(neo4j_session, "ChildNode", ["id"]) == {
        ("child-1",),
        ("child-2",),
    }


def _setup_parent_without_children(neo4j_session, lastupdated: int):
    """Create an InterestingAsset parent with NO children."""
    # Clean up any leftover ChildNodes from previous tests
    neo4j_session.run("MATCH (c:ChildNode) DETACH DELETE c")

    neo4j_session.run(MERGE_SUB_RESOURCE_QUERY)
    neo4j_session.run(MERGE_HELLO_ASSET_QUERY)
    neo4j_session.run(MERGE_WORLD_ASSET_QUERY)

    query = build_ingestion_query(InterestingAssetSchema())
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_WITH_ALL_RELS,
        lastupdated=lastupdated,
        sub_resource_id="sub-resource-id",
    )


def test_cascade_delete_works_for_childless_parents(neo4j_session):
    """
    Test cascade_delete=True still deletes parents that have no children.
    """
    _setup_parent_without_children(neo4j_session, lastupdated=1)

    # Verify parent exists and has no children
    assert check_nodes(neo4j_session, "InterestingAsset", ["id"]) == {
        ("interesting-node-id",),
    }
    assert check_nodes(neo4j_session, "ChildNode", ["id"]) == set()

    # Cleanup with cascade_delete=True should still delete the childless parent
    GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "sub-resource-id"},
        cascade_delete=True,
    ).run(neo4j_session)

    assert check_nodes(neo4j_session, "InterestingAsset", ["id"]) == set()


def test_cascade_delete_protects_reparented_children(neo4j_session):
    """
    Test that children re-parented in the current sync are NOT deleted.
    A child with lastupdated matching UPDATE_TAG was touched in this sync,
    so it should be preserved even if its old parent is stale.
    """
    _setup_parent_with_children(neo4j_session, lastupdated=1)

    # Simulate re-parenting: update one child's lastupdated to match the new UPDATE_TAG
    neo4j_session.run(
        """
        MATCH (c:ChildNode{id: 'child-1'})
        SET c.lastupdated = 2
        """,
    )

    # Cleanup with UPDATE_TAG=2 makes parent stale, but child-1 has lastupdated=2
    GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "sub-resource-id"},
        cascade_delete=True,
    ).run(neo4j_session)

    # Parent deleted, child-2 (stale) deleted, but child-1 (re-parented) preserved
    assert check_nodes(neo4j_session, "InterestingAsset", ["id"]) == set()
    assert check_nodes(neo4j_session, "ChildNode", ["id"]) == {("child-1",)}
