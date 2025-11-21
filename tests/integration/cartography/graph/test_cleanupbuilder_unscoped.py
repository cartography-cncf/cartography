from cartography.client.core.tx import load_graph_data
from cartography.graph.job import GraphJob
from cartography.graph.querybuilder import build_ingestion_query
from tests.data.graph.querybuilder.sample_models.allow_unscoped import (
    UnscopedNodeSchema,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def test_cleanup_unscoped_node_end_to_end(neo4j_session):
    """
    Arrange
        Create paths
        (u:UnscopedNode{id:'unscoped-node-id'})-[:RELATES_TO]->(:SimpleNode{id: 'simple-node-id'})
        at timestamp lastupdated 1.

    Act
        Run cleanup with UPDATE_TAG=2.

    Assert
        That the UnscopedNode is deleted because it was stale and had scoped_cleanup=False.
        The SimpleNode should remain since it's not part of the cleanup scope.
    """
    # Arrange: Create the SimpleNode first
    neo4j_session.run(
        """
        MERGE (s:SimpleNode{id: 'simple-node-id'})
        ON CREATE SET s.lastupdated = 1
        """
    )

    # Arrange: Create the UnscopedNode and its relationship to SimpleNode
    query = build_ingestion_query(UnscopedNodeSchema())
    load_graph_data(
        neo4j_session,
        query,
        [
            {
                "id": "unscoped-node-id",
                "name": "test-node",
                "simple_node_id": "simple-node-id",  # This will be used to create the RELATES_TO relationship
            }
        ],
        lastupdated=1,
    )

    # Sanity check: Verify that the relationship exists
    assert check_rels(
        neo4j_session,
        "UnscopedNode",
        "id",
        "SimpleNode",
        "id",
        "RELATES_TO",
        rel_direction_right=True,
    ) == {("unscoped-node-id", "simple-node-id")}

    # Act: Run the cleanup job with UPDATE_TAG=2
    cleanup_job = GraphJob.from_node_schema(
        UnscopedNodeSchema(),
        {"UPDATE_TAG": 2},
    )
    cleanup_job.run(neo4j_session)

    # Assert: The UnscopedNode should be deleted because it was stale and had scoped_cleanup=False
    assert check_nodes(neo4j_session, "UnscopedNode", ["id"]) == set()

    # Assert: The SimpleNode should still exist since it's not part of the cleanup scope
    assert check_nodes(neo4j_session, "SimpleNode", ["id"]) == {("simple-node-id",)}

    # Assert: The relationship should be gone since the UnscopedNode was deleted
    assert (
        check_rels(
            neo4j_session,
            "UnscopedNode",
            "id",
            "SimpleNode",
            "id",
            "RELATES_TO",
            rel_direction_right=True,
        )
        == set()
    )
