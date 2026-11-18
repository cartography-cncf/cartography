import pytest

from cartography.client.core.tx import load_graph_data
from cartography.graph.job import GraphJob
from cartography.graph.querybuilder import build_ingestion_query
from cartography.graph.statement import SCAN_BATCHES_PER_RUN
from tests.data.graph.querybuilder.sample_data.helloworld_relationships import (
    INTERESTING_NODE_NO_WORLD_ASSET,
)
from tests.data.graph.querybuilder.sample_data.helloworld_relationships import (
    INTERESTING_NODE_SUB_RES_ONLY,
)
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


# TODO: Once we have more real modules using cartography data objects, add a test using them instead of these fake objs.
def test_cleanup_interesting_asset_end_to_end_only_sub_res_remains(neo4j_session):
    """
    Arrange
        Create paths
        (i:InterestingAsset{id:'interesting-node-id'})<-[:RELATIONSHIP_LABEL]-(:SubResource{id:sub-resource-id}),
        (i)-[:ASSOCIATED_WITH]->(:HelloAsset{id: the-helloasset-id-1}),
        (i)<-[:CONNECTED]-(:WorldAsset{id: world-asset-id})
        at timestamp lastupdated 1.

    Act
        Suppose only InterestingAsset and its SubResource connection exist now at timestamp lastupdated=2.
        Run cleanup.

    Assert
        That only the rels to the InterestingAsset and SubResource exist and all other rels have been cleaned up.
    """
    # Arrange: add these nodes and rels to the graph, all with lastupdated=1:
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
    # Sanity checks to verify that the relationships exist.
    assert check_rels(
        neo4j_session,
        "InterestingAsset",
        "id",
        "WorldAsset",
        "id",
        "CONNECTED",
        rel_direction_right=False,
    ) == {("interesting-node-id", "the-worldasset-id-1")}

    assert check_rels(
        neo4j_session,
        "InterestingAsset",
        "id",
        "HelloAsset",
        "id",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {("interesting-node-id", "the-helloasset-id-1")}

    assert check_rels(
        neo4j_session,
        "InterestingAsset",
        "id",
        "SubResource",
        "id",
        "RELATIONSHIP_LABEL",
        rel_direction_right=False,
    ) == {("interesting-node-id", "sub-resource-id")}

    # Arrange: Suppose only InterestingAsset and its SubResource connection exist now at timestamp lastupdated=2.
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_SUB_RES_ONLY,
        lastupdated=2,
        sub_resource_id="sub-resource-id",
    )

    # Act: Now actually generate and run the cleanup job.
    cleanup_job = GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "sub-resource-id"},
        iterationsize=1,
    )
    cleanup_job.run(neo4j_session)

    # Assert
    # The rel between InterestingAsset and WorldAsset was stale (lastupdated != 2) and was cleaned up,
    assert (
        check_rels(
            neo4j_session,
            "InterestingAsset",
            "id",
            "WorldAsset",
            "id",
            "CONNECTED",
            rel_direction_right=True,
        )
        == set()
    )
    # but we don't delete the WorldAsset itself, as that cleanup should be handled by the WorldAsset's own intel module.
    assert check_nodes(neo4j_session, "WorldAsset", ["id"]) == {
        ("the-worldasset-id-1",),
    }

    # Same thing here: the rel between InterestingAsset and HelloAsset was stale (lastupdated != 2) and was cleaned up,
    assert (
        check_rels(
            neo4j_session,
            "InterestingAsset",
            "id",
            "HelloAsset",
            "id",
            "ASSOCIATED_WITH",
            rel_direction_right=False,
        )
        == set()
    )
    # but we don't delete the HelloAsset itself, as that cleanup should be handled by the HelloAsset's own intel module.
    assert check_nodes(neo4j_session, "HelloAsset", ["id"]) == {
        ("the-helloasset-id-1",),
    }

    # This is the only rel we expect to remain intact as it was last updated in our call to `load_graph_data()` above.
    assert check_rels(
        neo4j_session,
        "InterestingAsset",
        "id",
        "SubResource",
        "id",
        "RELATIONSHIP_LABEL",
        rel_direction_right=False,
    ) == {("interesting-node-id", "sub-resource-id")}
    # And we expect to be able to retrieve fields from the InterestingAsset,
    assert check_nodes(
        neo4j_session,
        "InterestingAsset",
        ["id", "property1", "property2", "lastupdated"],
    ) == {
        ("interesting-node-id", "b", "c", 2),
    }
    # and from the SubResource:
    assert check_nodes(neo4j_session, "SubResource", ["id", "lastupdated"]) == {
        ("sub-resource-id", 1),
    }


def test_cleanup_interesting_asset_end_to_end_no_world_asset(neo4j_session):
    """
    Arrange
        Create paths
        (i:InterestingAsset{id:'interesting-node-id'})<-[:RELATIONSHIP_LABEL]-(:SubResource{id:sub-resource-id}),
        (i)-[:ASSOCIATED_WITH]->(:HelloAsset{id: the-helloasset-id-1}),
        (i)<-[:CONNECTED]-(:WorldAsset{id: world-asset-id})
        at timestamp lastupdated 1.

    Act
        Suppose all nodes except for WorldAsset exist at timestamp lastupdated=2.
        Run cleanup.

    Assert
        That only the relationship to the WorldAsset has been cleaned up.
    """
    # Arrange: add these nodes and rels to the graph, all with lastupdated=1:
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
    # Sanity checks to verify that the relationships exist.
    assert check_rels(
        neo4j_session,
        "InterestingAsset",
        "id",
        "WorldAsset",
        "id",
        "CONNECTED",
        rel_direction_right=False,
    ) == {("interesting-node-id", "the-worldasset-id-1")}

    assert check_rels(
        neo4j_session,
        "InterestingAsset",
        "id",
        "HelloAsset",
        "id",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {("interesting-node-id", "the-helloasset-id-1")}

    assert check_rels(
        neo4j_session,
        "InterestingAsset",
        "id",
        "SubResource",
        "id",
        "RELATIONSHIP_LABEL",
        rel_direction_right=False,
    ) == {("interesting-node-id", "sub-resource-id")}

    # Arrange: Suppose all assets except the WorldAsset exist now at timestamp lastupdated=2.
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_NO_WORLD_ASSET,
        lastupdated=2,
        sub_resource_id="sub-resource-id",
    )

    # Act: Now actually generate and run the cleanup job.
    cleanup_job = GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "sub-resource-id"},
        iterationsize=1,
    )
    cleanup_job.run(neo4j_session)

    # Assert
    # The rel between InterestingAsset and WorldAsset was stale (lastupdated != 2) and was cleaned up,
    assert (
        check_rels(
            neo4j_session,
            "InterestingAsset",
            "id",
            "WorldAsset",
            "id",
            "CONNECTED",
            rel_direction_right=True,
        )
        == set()
    )
    # but we don't delete the WorldAsset itself, as that cleanup should be handled by the WorldAsset's own intel module.
    assert check_nodes(neo4j_session, "WorldAsset", ["id"]) == {
        ("the-worldasset-id-1",),
    }

    # The rel between InterestingAsset and HelloAsset should still exist.
    assert check_rels(
        neo4j_session,
        "InterestingAsset",
        "id",
        "HelloAsset",
        "id",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {("interesting-node-id", "the-helloasset-id-1")}

    # We also expect the sub resource relationship to remain intact.
    assert check_rels(
        neo4j_session,
        "InterestingAsset",
        "id",
        "SubResource",
        "id",
        "RELATIONSHIP_LABEL",
        rel_direction_right=False,
    ) == {("interesting-node-id", "sub-resource-id")}
    # And we expect to be able to retrieve fields from the InterestingAsset,
    assert check_nodes(
        neo4j_session,
        "InterestingAsset",
        ["id", "property1", "property2", "lastupdated"],
    ) == {
        ("interesting-node-id", "b", "c", 2),
    }
    # and from the SubResource:
    assert check_nodes(neo4j_session, "SubResource", ["id", "lastupdated"]) == {
        ("sub-resource-id", 1),
    }


def test_cleanup_runs_until_every_stale_node_is_gone(neo4j_session):
    # Arrange: more stale nodes than a single cleanup scan deletes.
    neo4j_session.run(MERGE_SUB_RESOURCE_QUERY)
    query = build_ingestion_query(InterestingAssetSchema())
    stale = [
        {**INTERESTING_NODE_SUB_RES_ONLY[0], "Id": f"stale-asset-{i}"}
        for i in range(SCAN_BATCHES_PER_RUN + 50)
    ]
    load_graph_data(
        neo4j_session, query, stale, lastupdated=10, sub_resource_id="sub-resource-id"
    )
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_SUB_RES_ONLY,
        lastupdated=11,
        sub_resource_id="sub-resource-id",
    )

    # Act
    GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 11, "sub_resource_id": "sub-resource-id"},
        iterationsize=1,
    ).run(neo4j_session)

    # Assert
    assert check_nodes(neo4j_session, "InterestingAsset", ["id", "lastupdated"]) == {
        ("interesting-node-id", 11),
    }


def _count(neo4j_session, query: str, **params) -> int:
    return neo4j_session.run(query, **params).single()["c"]


def _seed_hub_graph(neo4j_session) -> None:
    """
    Seed two scopes, each with a sub resource, so cleanup for 'scope-a' at UPDATE_TAG=2 sees:
      - stale-hub (lastupdated=1) in scope-a: many relationships of several types, including
        same-type RELATIONSHIP_LABEL edges to children and an edge to another stale node
      - stale-peer (lastupdated=1) in scope-a: linked to stale-hub, so one relationship is
        reachable from two stale nodes
      - fresh (lastupdated=2) in scope-a: must keep everything
      - other-scope-stale (lastupdated=1) in scope-b: must keep everything
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        UNWIND [{sub: 'scope-a', lu: 1}, {sub: 'scope-b', lu: 1}] AS scope
        MERGE (s:SubResource{id: scope.sub}) SET s.lastupdated = scope.lu
        """,
    )
    neo4j_session.run(
        """
        UNWIND [
            {id: 'stale-hub', sub: 'scope-a', lu: 1},
            {id: 'stale-peer', sub: 'scope-a', lu: 1},
            {id: 'fresh', sub: 'scope-a', lu: 2},
            {id: 'other-scope-stale', sub: 'scope-b', lu: 1}
        ] AS a
        MERGE (n:InterestingAsset{id: a.id}) SET n.lastupdated = a.lu
        WITH n, a
        MATCH (s:SubResource{id: a.sub})
        MERGE (s)-[r:RELATIONSHIP_LABEL]->(n) SET r.lastupdated = a.lu
        """,
    )
    neo4j_session.run(
        """
        UNWIND ['stale-hub', 'stale-peer', 'fresh', 'other-scope-stale'] AS asset_id
        MATCH (n:InterestingAsset{id: asset_id})
        UNWIND range(1, 5) AS i
        MERGE (h:HelloAsset{id: asset_id + '-hello-' + toString(i)}) SET h.lastupdated = n.lastupdated
        MERGE (n)-[r:ASSOCIATED_WITH]->(h) SET r.lastupdated = n.lastupdated
        """,
    )
    # Children hang off the assets by the same type as the sub resource relationship, in the
    # opposite direction: (:InterestingAsset)-[:RELATIONSHIP_LABEL]->(:ChildNode).
    neo4j_session.run(
        """
        UNWIND ['stale-hub', 'fresh', 'other-scope-stale'] AS asset_id
        MATCH (n:InterestingAsset{id: asset_id})
        UNWIND range(1, 5) AS i
        MERGE (c:ChildNode{id: asset_id + '-child-' + toString(i)}) SET c.lastupdated = n.lastupdated
        MERGE (n)-[r:RELATIONSHIP_LABEL]->(c) SET r.lastupdated = n.lastupdated
        """,
    )
    neo4j_session.run(
        """
        MATCH (a:InterestingAsset{id: 'stale-hub'}), (b:InterestingAsset{id: 'stale-peer'})
        MERGE (a)-[r:LINKS_TO]->(b) SET r.lastupdated = 1
        """,
    )


def _assert_only_untouched_assets_remain(neo4j_session) -> None:
    assert check_nodes(neo4j_session, "InterestingAsset", ["id"]) == {
        ("fresh",),
        ("other-scope-stale",),
    }
    # The fresh and the out-of-scope asset keep their sub resource link and relationships.
    for asset_id in ("fresh", "other-scope-stale"):
        assert (
            _count(
                neo4j_session,
                """
                MATCH (:InterestingAsset{id: $id})-[r:ASSOCIATED_WITH]->(:HelloAsset)
                RETURN count(r) AS c
                """,
                id=asset_id,
            )
            == 5
        )
        assert (
            _count(
                neo4j_session,
                """
                MATCH (:InterestingAsset{id: $id})-[r:RELATIONSHIP_LABEL]->(:ChildNode)
                RETURN count(r) AS c
                """,
                id=asset_id,
            )
            == 5
        )
        assert (
            _count(
                neo4j_session,
                """
                MATCH (:SubResource)-[r:RELATIONSHIP_LABEL]->(:InterestingAsset{id: $id})
                RETURN count(r) AS c
                """,
                id=asset_id,
            )
            == 1
        )


@pytest.mark.parametrize("iterationsize", [1, 2])
def test_cleanup_removes_stale_node_and_every_relationship_in_small_batches(
    neo4j_session,
    iterationsize,
):
    """
    A stale node with more relationships than the batch size is deleted together with all of
    its relationships, while fresh nodes and stale nodes in another scope are untouched.
    """
    _seed_hub_graph(neo4j_session)

    GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "scope-a"},
        iterationsize=iterationsize,
    ).run(neo4j_session)

    _assert_only_untouched_assets_remain(neo4j_session)
    # The children are not owned by the stale asset (no cascade_delete), so they stay.
    assert _count(neo4j_session, "MATCH (c:ChildNode) RETURN count(c) AS c") == 15
    # Nothing is left pointing at the deleted assets.
    assert (
        _count(
            neo4j_session,
            "MATCH ()-[r:LINKS_TO]-() RETURN count(r) AS c",
        )
        == 0
    )


def test_cleanup_detach_pass_leaves_only_the_parent_link(neo4j_session):
    """
    The detach pass runs on its own: it removes the relationships of stale nodes, including
    same-type edges to children, but leaves the nodes and the link the node delete needs.
    """
    _seed_hub_graph(neo4j_session)
    job = GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "scope-a"},
        iterationsize=2,
    )

    job.statements[0].run(neo4j_session)

    assert check_nodes(neo4j_session, "InterestingAsset", ["id"]) == {
        ("stale-hub",),
        ("stale-peer",),
        ("fresh",),
        ("other-scope-stale",),
    }
    for asset_id in ("stale-hub", "stale-peer"):
        remaining = neo4j_session.run(
            """
            MATCH (:InterestingAsset{id: $id})-[r]-()
            RETURN type(r) AS type, count(r) AS c
            """,
            id=asset_id,
        ).data()
        assert remaining == [{"type": "RELATIONSHIP_LABEL", "c": 1}]
    # The out-of-scope stale node is not in this cleanup's scope, so it is not detached.
    assert (
        _count(
            neo4j_session,
            "MATCH (:InterestingAsset{id: 'other-scope-stale'})-[r]-() RETURN count(r) AS c",
        )
        == 11
    )


def test_cleanup_with_cascade_delete_removes_stale_node_children_and_relationships(
    neo4j_session,
):
    """
    cascade_delete still reaches the children through same-type relationships: the detach
    pass must leave those in place.
    """
    _seed_hub_graph(neo4j_session)
    job = GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "scope-a"},
        iterationsize=2,
        cascade_delete=True,
    )

    job.statements[0].run(neo4j_session)
    assert (
        _count(
            neo4j_session,
            """
            MATCH (:InterestingAsset{id: 'stale-hub'})-[r:RELATIONSHIP_LABEL]->(:ChildNode)
            RETURN count(r) AS c
            """,
        )
        == 5
    )

    job.run(neo4j_session)

    _assert_only_untouched_assets_remain(neo4j_session)
    # stale-hub's children are gone; the other assets' children remain.
    assert check_nodes(neo4j_session, "ChildNode", ["id"]) == {
        (f"{asset_id}-child-{i}",)
        for asset_id in ("fresh", "other-scope-stale")
        for i in range(1, 6)
    }
