from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from tests.data.graph.querybuilder.sample_data.multiple_attr_match import MERGE_PERSONS
from tests.data.graph.querybuilder.sample_data.multiple_attr_match import TEST_COMPUTERS
from tests.data.graph.querybuilder.sample_models.multiple_attr_match import TestComputer


def test_load_graph_data_match_on_multiple_attrs(neo4j_session):
    """
    Test load_graph_data() if we have a relationship that matches on more than one attribute.

    In this test case, Persons can OWN TestComputers, and this assignment is made based on both first_name and
    last_name.
    """
    # Arrange: add (:SubResource{id:sub-resource-id}) and (:WorldAsset{id: world-asset-id}) to the test graph
    neo4j_session.run(MERGE_PERSONS)

    # Act
    query = build_ingestion_query(TestComputer())
    load_graph_data(
        neo4j_session,
        query,
        TEST_COMPUTERS,
        lastupdated=1,
    )

    # Assert that Homer has 2 computers and Lisa has 1 computer
    expected = {
        ("server-in-the-closet", "Homer"),
        ("beefy-box", "Homer"),
        ("macbook-air", "Lisa"),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:TestComputer)<-[:OWNS]-(n2:Person) RETURN n1.name, n2.first_name;
        """,
    )
    actual = {(r["n1.name"], r["n2.first_name"]) for r in result}
    assert actual == expected
