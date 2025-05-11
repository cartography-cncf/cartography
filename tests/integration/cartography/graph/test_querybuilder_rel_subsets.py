from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from tests.data.graph.querybuilder.sample_data.helloworld_relationships import (
    INTERESTING_NODE_WITH_PARTIAL_RELS,
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


def test_load_graph_data_subset_of_relationships(neo4j_session):
    """
    Test load_graph_data() if a schema defines multiple relationships but only a subset of them are possible to create
    given our data.

    In this test case, the following relationships are possible:
        (:InterestingAsset)<-[:RELATIONSHIP_LABEL]-(:SubResource)
        (:InterestingAsset)-[:ASSOCIATED_WITH]->(:HelloAsset)
        (:InterestingAsset)<-[:CONNECTED]-(:WorldAsset)
    but our test data does not include a HelloAsset.
    """
    # Arrange: add (:SubResource{id:sub-resource-id}) and (:WorldAsset{id: world-asset-id}) to the test graph
    neo4j_session.run(MERGE_SUB_RESOURCE_QUERY)
    neo4j_session.run(MERGE_WORLD_ASSET_QUERY)

    # Act
    query = build_ingestion_query(InterestingAssetSchema())
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_WITH_PARTIAL_RELS,
        lastupdated=1,
        sub_resource_id="sub-resource-id",
    )

    # Assert that the InterestingAsset to SubResource relationship exists
    expected = {
        ("interesting-node-id", "sub-resource-id"),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:InterestingAsset)<-[:RELATIONSHIP_LABEL]-(n2:SubResource) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual == expected

    # Assert that the InterestingAsset to HelloAsset relationship does NOT exist
    expected = {
        ("interesting-node-id", None),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:InterestingAsset)
        OPTIONAL MATCH (n1)--(n2:HelloAsset)
        RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual == expected

    # Assert that the InterestingAsset to WorldAsset relationship exists
    expected = {
        ("interesting-node-id", "the-worldasset-id-1"),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:InterestingAsset)<-[:CONNECTED]-(n2:WorldAsset) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual == expected


def test_load_graph_data_subset_of_relationships_only_sub_resource(neo4j_session):
    """
    In this test case, our test data only includes the sub resource relationship
    """
    # Arrange: add (:SubResource{id:sub-resource-id})
    neo4j_session.run("MATCH (n) DETACH DELETE n;")
    neo4j_session.run(MERGE_SUB_RESOURCE_QUERY)

    # Act
    query = build_ingestion_query(InterestingAssetSchema())
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_WITH_PARTIAL_RELS,
        lastupdated=1,
        sub_resource_id="sub-resource-id",
    )

    # Assert that the InterestingAsset to SubResource relationship exists
    expected = {
        ("interesting-node-id", "sub-resource-id"),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:InterestingAsset)<-[:RELATIONSHIP_LABEL]-(n2:SubResource) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual == expected

    # Assert that the InterestingAsset to HelloAsset relationship does NOT exist
    expected = {
        ("interesting-node-id", None),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:InterestingAsset)
        OPTIONAL MATCH (n1)--(n2:HelloAsset)
        RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual == expected

    # Assert that the InterestingAsset to WorldAsset relationship does NOT exist
    expected = {
        ("interesting-node-id", None),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:InterestingAsset)
        OPTIONAL MATCH (n1)<-[:CONNECTED]-(n2:WorldAsset)
        RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual == expected
