from cartography.client.core.tx import load_graph_data
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
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetToSubResourceRel,
)
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetToWorldAssetRel,
)


def test_load_graph_data_extra_node_labels_and_no_relationships(neo4j_session):
    """
    Test that
    - multiple labels defined on a CartographyNodeSchema are properly recorded to the graph.
    - we are able to generate a query that includes no relationships in build_ingestion_query()'s
      `selected_relationships` parameter.
    """
    # Act: specify the empty set as selected_relationships to build_ingestion_query().
    query = build_ingestion_query(
        InterestingAssetSchema(),
        selected_relationships=set(),
    )

    # Act: call `load_graph_data()` without specifying `sub_resource` or any other kwargs that were present on
    # InterestingAsset's attached RelSchema.
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_WITH_ALL_RELS,
        lastupdated=1,
    )

    # Assert that the labels exist
    expected = {"AnotherNodeLabel", "InterestingAsset", "YetAnotherNodeLabel"}
    result = neo4j_session.run(
        """
        MATCH (n1:InterestingAsset) RETURN labels(n1) AS labels;
        """,
    )
    actual = {label for label in result.data()[0]["labels"]}
    assert actual == expected


def test_load_graph_data_with_sub_rel_selected(neo4j_session):
    """
    Test generating and running a query that includes only InterestingAssetSchema.sub_resource_relationship in
    build_ingestion_query()'s selected_relationships parameter.
    """
    # Arrange: add (:SubResource{id:sub-resource-id}) and (:WorldAsset{id: world-asset-id}) to the test graph
    neo4j_session.run(MERGE_SUB_RESOURCE_QUERY)
    neo4j_session.run(MERGE_HELLO_ASSET_QUERY)
    neo4j_session.run(MERGE_WORLD_ASSET_QUERY)

    # Act
    query = build_ingestion_query(
        InterestingAssetSchema(),
        selected_relationships={
            InterestingAssetToSubResourceRel(),
        },
    )
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_WITH_ALL_RELS,
        lastupdated=1,
        sub_resource_id="sub-resource-id",
    )

    # Assert that the InterestingAsset to SubResource relationship exists.
    expected = {("interesting-node-id", "sub-resource-id")}
    result = neo4j_session.run(
        """
        MATCH (n1:InterestingAsset)<-[:RELATIONSHIP_LABEL]-(n2:SubResource) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual == expected


def test_load_graph_data_with_worldasset_rel_selected(neo4j_session):
    """
    Test generating and running a query that specifies only 1 of 2 of the rels in
    InterestingAssetSchema.other_relationships to build_ingestion_query()'s selected_relationships parameter.
    """
    # Arrange: add (:SubResource{id:sub-resource-id}) and (:WorldAsset{id: world-asset-id}) to the test graph
    neo4j_session.run(MERGE_SUB_RESOURCE_QUERY)
    neo4j_session.run(MERGE_HELLO_ASSET_QUERY)
    neo4j_session.run(MERGE_WORLD_ASSET_QUERY)

    # Act
    query = build_ingestion_query(
        InterestingAssetSchema(),
        selected_relationships={
            InterestingAssetToWorldAssetRel(),
        },
    )
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_WITH_ALL_RELS,
        lastupdated=1,
    )

    # Assert that the InterestingAsset to WorldAsset relationship exists
    expected = {("interesting-node-id", "the-worldasset-id-1")}
    result = neo4j_session.run(
        """
        MATCH (n1:InterestingAsset)<-[:CONNECTED]-(n2:WorldAsset) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual == expected


def test_load_graph_data_with_sub_resource_and_worldasset_rel_selected(neo4j_session):
    """
    Test generating and running a query that includes InterestingAssetSchema.sub_resource_relationship + only 1 of 2 of
    the rels in InterestingAssetSchema.other_relationships to build_ingestion_query()'s selected_relationships
    parameter.
    """
    # Arrange: add (:SubResource{id:sub-resource-id}) and (:WorldAsset{id: world-asset-id}) to the test graph
    neo4j_session.run(MERGE_SUB_RESOURCE_QUERY)
    neo4j_session.run(MERGE_HELLO_ASSET_QUERY)
    neo4j_session.run(MERGE_WORLD_ASSET_QUERY)

    # Act
    query = build_ingestion_query(
        InterestingAssetSchema(),
        selected_relationships={
            InterestingAssetToSubResourceRel(),
            InterestingAssetToWorldAssetRel(),
        },
    )
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_WITH_ALL_RELS,
        lastupdated=1,
        sub_resource_id="sub-resource-id",
    )

    # Assert that the InterestingAsset to WorldAsset relationship exists
    expected = {("interesting-node-id", "the-worldasset-id-1")}
    result = neo4j_session.run(
        """
        MATCH (n1:InterestingAsset)<-[:CONNECTED]-(n2:WorldAsset) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual == expected

    # Assert that the InterestingAsset to SubResource relationship exists.
    expected = {("interesting-node-id", "sub-resource-id")}
    result = neo4j_session.run(
        """
        MATCH (n1:InterestingAsset)<-[:RELATIONSHIP_LABEL]-(n2:SubResource) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual == expected

    # Assert that the InterestingAsset to Hello relationships does NOT exist.
    expected = set()
    result = neo4j_session.run(
        """
        MATCH (n1:InterestingAsset)-[:ASSOCIATED_WITH]->(n2:HelloAsset) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual == expected
