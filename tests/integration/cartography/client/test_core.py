from cartography.client.core.tx import ensure_indexes
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.client.core.tx import read_list_of_tuples_tx
from cartography.client.core.tx import read_list_of_values_tx
from cartography.client.core.tx import read_single_dict_tx
from cartography.client.core.tx import read_single_value_tx
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetSchema,
)


def _ensure_test_data(neo4j_session):
    neo4j_session.run(
        """
            MERGE (t1:TestNode{name: "Homer", age: 39})
            MERGE (t2:TestNode{name: "Lisa", age: 8})
            MERGE (t3:TestNode{name: "Marge", age: 36})
        """,
    )


def test_read_list_of_values_tx(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = "MATCH (a:TestNode) RETURN a.name ORDER BY a.name"
    values = neo4j_session.read_transaction(read_list_of_values_tx, query)

    # Assert
    assert values == ["Homer", "Lisa", "Marge"]


def test_read_list_of_values_tx_assert_returns_first_field_only(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act: test a query string that returns more than one field
    query = "MATCH (a:TestNode) RETURN a.name, a.age ORDER BY a.name"
    values = neo4j_session.read_transaction(read_list_of_values_tx, query)

    # Assert that only the first field is returned for each value in the list.
    assert values == ["Homer", "Lisa", "Marge"]


def test_read_single_value_tx(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = """MATCH (a:TestNode{name: "Lisa"}) RETURN a.age"""
    value = neo4j_session.read_transaction(read_single_value_tx, query)

    # Assert
    assert value == 8


def test_read_single_value_tx_assert_returns_first_of_list_only(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = """MATCH (a:TestNode) RETURN a.age ORDER BY a.age"""
    value = neo4j_session.read_transaction(read_single_value_tx, query)

    # Assert that we only return the first value if the query happesn to return more than one value
    assert value == 8


def test_read_list_of_dicts_tx(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = "MATCH (a:TestNode) RETURN a.name AS name, a.age AS age ORDER BY age"
    data = neo4j_session.read_transaction(read_list_of_dicts_tx, query)

    # Assert
    assert len(data) == 3
    assert data[0]["name"] == "Lisa"
    assert {"name": "Homer", "age": 39} in data


def test_read_single_dict_tx(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = """MATCH (a:TestNode{name: "Homer"}) RETURN a.name AS name, a.age AS age"""
    result = neo4j_session.read_transaction(read_single_dict_tx, query)

    # Assert
    assert {"name": "Homer", "age": 39} == result


def test_read_single_dict_tx_assert_return_first_of_list_only(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = """MATCH (a:TestNode) RETURN a.name AS name, a.age AS age ORDER BY age"""
    result = neo4j_session.read_transaction(read_single_dict_tx, query)

    # Assert that this func returns the first item of the list and not the whole list
    assert {"name": "Lisa", "age": 8} == result


def test_read_list_of_tuples_tx(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = "MATCH (a:TestNode) RETURN a.name AS name, a.age AS age ORDER BY age"
    data = neo4j_session.read_transaction(read_list_of_tuples_tx, query)

    # Assert
    assert len(data) == 3
    assert data[0][0] == "Lisa"


def test_ensure_indexes(neo4j_session):
    # Act
    ensure_indexes(neo4j_session, InterestingAssetSchema())

    # Assert: check the test database for indexes
    indexes = neo4j_session.run(
        """
        SHOW ALL INDEXES
        WHERE
            "InterestingAsset" in labelsOrTypes OR
            "HelloAsset" in labelsOrTypes OR
            "WorldAsset" in labelsOrTypes
    """,
    ).data()
    assert len(indexes) == 4

    # Assert there is 1 label for each index created (Neo4j's data-shape of `SHOW ALL INDEXES` is weird)
    for item in indexes:
        assert len(item["labelsOrTypes"]) == 1

    # Assert all the node labels involved in the InterestingAsset's relationships are indexed
    labels = {item["labelsOrTypes"][0] for item in indexes}
    assert labels == {"InterestingAsset", "HelloAsset", "WorldAsset"}

    # Assert there is 1 property for each index created (again, Neo4j's data-shape of `SHOW ALL INDEXES` is weird)
    for item in indexes:
        assert len(item["properties"]) == 1

    # Assert that the indexed property for all 3 node labels is as expected (`id` in this case)
    indexed_fields = {item["properties"][0] for item in indexes}
    assert indexed_fields == {"id", "lastupdated"}
