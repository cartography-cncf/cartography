"""
Integration tests for cascade_delete cleanup feature.

Tests the core behavior: when cascade_delete=True, deleting a stale parent
also deletes its children (nodes with RESOURCE relationships from the parent).
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
    """Create an InterestingAsset parent with two child nodes connected via RESOURCE."""
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

    # Create children with RESOURCE relationship from parent: (Parent)-[:RESOURCE]->(Child)
    neo4j_session.run(
        """
        UNWIND ['child-1', 'child-2'] AS child_id
        MERGE (c:ChildNode{id: child_id})
        SET c.lastupdated = $lastupdated
        WITH c
        MATCH (p:InterestingAsset{id: 'interesting-node-id'})
        MERGE (p)-[:RESOURCE]->(c)
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
