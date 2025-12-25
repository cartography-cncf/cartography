"""Integration tests for cascade_delete feature in cleanup builder."""

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
from tests.integration.util import check_rels


def _create_child_nodes_with_resource_rel(
    neo4j_session, parent_id: str, lastupdated: int
):
    """
    Create child nodes that have RESOURCE relationships from the parent InterestingAsset.
    In Cartography, RESOURCE relationships point from parent to child: (Parent)-[:RESOURCE]->(Child).
    This simulates a hierarchical relationship like GitLab Organization -> Groups -> Projects.
    """
    neo4j_session.run(
        """
        MERGE (c1:ChildNode{id: 'child-1'})
        SET c1.lastupdated = $lastupdated,
            c1.name = 'Child One'
        WITH c1
        MATCH (p:InterestingAsset{id: $parent_id})
        MERGE (p)-[:RESOURCE]->(c1)
        """,
        parent_id=parent_id,
        lastupdated=lastupdated,
    )
    neo4j_session.run(
        """
        MERGE (c2:ChildNode{id: 'child-2'})
        SET c2.lastupdated = $lastupdated,
            c2.name = 'Child Two'
        WITH c2
        MATCH (p:InterestingAsset{id: $parent_id})
        MERGE (p)-[:RESOURCE]->(c2)
        """,
        parent_id=parent_id,
        lastupdated=lastupdated,
    )


def test_cascade_delete_removes_children(neo4j_session):
    """
    Test that cascade_delete=True removes child nodes with RESOURCE relationships
    when the parent node is stale.

    Arrange:
        - Create InterestingAsset (parent) at lastupdated=1
        - Create ChildNode nodes with InterestingAsset-[:RESOURCE]->ChildNode relationships

    Act:
        - Create new InterestingAsset at lastupdated=2 (making old one stale)
        - Run cleanup with cascade_delete=True

    Assert:
        - Stale parent is deleted
        - Child nodes are ALSO deleted (cascade)
    """
    # Arrange: Create the parent node and related assets at lastupdated=1
    neo4j_session.run(MERGE_SUB_RESOURCE_QUERY)
    neo4j_session.run(MERGE_HELLO_ASSET_QUERY)
    neo4j_session.run(MERGE_WORLD_ASSET_QUERY)

    query = build_ingestion_query(InterestingAssetSchema())
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_WITH_ALL_RELS,
        lastupdated=1,
        sub_resource_id="sub-resource-id",
    )

    # Create child nodes with RESOURCE relationships to the parent
    _create_child_nodes_with_resource_rel(
        neo4j_session, "interesting-node-id", lastupdated=1
    )

    # Sanity check: verify child nodes exist and have RESOURCE relationship from parent
    assert check_nodes(neo4j_session, "ChildNode", ["id"]) == {
        ("child-1",),
        ("child-2",),
    }
    # In Cartography, RESOURCE points from parent to child: (Parent)-[:RESOURCE]->(Child)
    assert check_rels(
        neo4j_session,
        "InterestingAsset",
        "id",
        "ChildNode",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("interesting-node-id", "child-1"),
        ("interesting-node-id", "child-2"),
    }

    # Act: Make the parent stale by not updating it (we just run cleanup with UPDATE_TAG=2)
    # Note: We don't create a new version at lastupdated=2, so the parent becomes stale

    cleanup_job = GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "sub-resource-id"},
        iterationsize=100,
        cascade_delete=True,  # Enable cascade delete
    )
    cleanup_job.run(neo4j_session)

    # Assert: Parent should be deleted (it was stale - lastupdated=1, not 2)
    assert check_nodes(neo4j_session, "InterestingAsset", ["id"]) == set()

    # Assert: Child nodes should ALSO be deleted due to cascade_delete=True
    assert check_nodes(neo4j_session, "ChildNode", ["id"]) == set()


def test_no_cascade_delete_preserves_children(neo4j_session):
    """
    Test that cascade_delete=False (default) does NOT remove child nodes
    when the parent node is deleted.

    Arrange:
        - Create InterestingAsset (parent) at lastupdated=1
        - Create ChildNode nodes with InterestingAsset-[:RESOURCE]->ChildNode relationships

    Act:
        - Run cleanup with cascade_delete=False (default)

    Assert:
        - Stale parent is deleted
        - Child nodes REMAIN (orphaned but not deleted)
    """
    # Arrange: Create the parent node and related assets at lastupdated=1
    neo4j_session.run(MERGE_SUB_RESOURCE_QUERY)
    neo4j_session.run(MERGE_HELLO_ASSET_QUERY)
    neo4j_session.run(MERGE_WORLD_ASSET_QUERY)

    query = build_ingestion_query(InterestingAssetSchema())
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_WITH_ALL_RELS,
        lastupdated=1,
        sub_resource_id="sub-resource-id",
    )

    # Create child nodes with RESOURCE relationships to the parent
    _create_child_nodes_with_resource_rel(
        neo4j_session, "interesting-node-id", lastupdated=1
    )

    # Sanity check: verify child nodes exist
    assert check_nodes(neo4j_session, "ChildNode", ["id"]) == {
        ("child-1",),
        ("child-2",),
    }

    # Act: Run cleanup WITHOUT cascade_delete (default is False)
    cleanup_job = GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "sub-resource-id"},
        iterationsize=100,
        cascade_delete=False,  # Explicitly set to False (this is also the default)
    )
    cleanup_job.run(neo4j_session)

    # Assert: Parent should be deleted (it was stale)
    assert check_nodes(neo4j_session, "InterestingAsset", ["id"]) == set()

    # Assert: Child nodes should REMAIN (not deleted because cascade_delete=False)
    # They are now orphaned (no parent) but still exist
    assert check_nodes(neo4j_session, "ChildNode", ["id"]) == {
        ("child-1",),
        ("child-2",),
    }


def test_cascade_delete_only_affects_stale_parents(neo4j_session):
    """
    Test that cascade_delete only affects children of STALE parents,
    not children of up-to-date parents.

    Arrange:
        - Create InterestingAsset at lastupdated=1
        - Create child nodes
        - Update InterestingAsset to lastupdated=2 (making it current)

    Act:
        - Run cleanup with UPDATE_TAG=2 and cascade_delete=True

    Assert:
        - Parent remains (it's current)
        - Child nodes remain (parent wasn't deleted)
    """
    # Arrange: Create the parent node at lastupdated=1
    neo4j_session.run(MERGE_SUB_RESOURCE_QUERY)
    neo4j_session.run(MERGE_HELLO_ASSET_QUERY)
    neo4j_session.run(MERGE_WORLD_ASSET_QUERY)

    query = build_ingestion_query(InterestingAssetSchema())
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_WITH_ALL_RELS,
        lastupdated=1,
        sub_resource_id="sub-resource-id",
    )

    # Create child nodes
    _create_child_nodes_with_resource_rel(
        neo4j_session, "interesting-node-id", lastupdated=1
    )

    # Update the parent to lastupdated=2 (making it current)
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_WITH_ALL_RELS,
        lastupdated=2,
        sub_resource_id="sub-resource-id",
    )

    # Act: Run cleanup with cascade_delete=True
    cleanup_job = GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "sub-resource-id"},
        iterationsize=100,
        cascade_delete=True,
    )
    cleanup_job.run(neo4j_session)

    # Assert: Parent should remain (it's current - lastupdated=2)
    assert check_nodes(neo4j_session, "InterestingAsset", ["id", "lastupdated"]) == {
        ("interesting-node-id", 2),
    }

    # Assert: Child nodes should remain (parent wasn't deleted)
    assert check_nodes(neo4j_session, "ChildNode", ["id"]) == {
        ("child-1",),
        ("child-2",),
    }


def test_cascade_delete_default_behavior_is_no_cascade(neo4j_session):
    """
    Test that the default behavior (not specifying cascade_delete) is to NOT cascade.
    This ensures backward compatibility.
    """
    # Arrange
    neo4j_session.run(MERGE_SUB_RESOURCE_QUERY)
    neo4j_session.run(MERGE_HELLO_ASSET_QUERY)
    neo4j_session.run(MERGE_WORLD_ASSET_QUERY)

    query = build_ingestion_query(InterestingAssetSchema())
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_WITH_ALL_RELS,
        lastupdated=1,
        sub_resource_id="sub-resource-id",
    )

    _create_child_nodes_with_resource_rel(
        neo4j_session, "interesting-node-id", lastupdated=1
    )

    # Act: Run cleanup WITHOUT specifying cascade_delete (should default to False)
    cleanup_job = GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "sub-resource-id"},
        iterationsize=100,
        # cascade_delete not specified - should default to False
    )
    cleanup_job.run(neo4j_session)

    # Assert: Parent deleted, but children remain (default is no cascade)
    assert check_nodes(neo4j_session, "InterestingAsset", ["id"]) == set()
    assert check_nodes(neo4j_session, "ChildNode", ["id"]) == {
        ("child-1",),
        ("child-2",),
    }
