from cartography.client.core.tx import load_graph_data
from cartography.graph.job import GraphJob
from cartography.graph.querybuilder import build_ingestion_query
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
