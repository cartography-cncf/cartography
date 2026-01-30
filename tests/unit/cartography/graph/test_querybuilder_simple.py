from cartography.graph.querybuilder import _get_cartography_version
from cartography.graph.querybuilder import _get_module_from_schema
from cartography.graph.querybuilder import build_ingestion_query
from tests.data.graph.querybuilder.sample_models.fake_emps_githubusers import (
    FakeEmpSchema,
)
from tests.data.graph.querybuilder.sample_models.fake_emps_githubusers_fuzzy import (
    FakeEmp2Schema,
)
from tests.data.graph.querybuilder.sample_models.simple_node import SimpleNodeSchema
from tests.data.graph.querybuilder.sample_models.simple_node import (
    SimpleNodeWithSubResourceSchema,
)
from tests.unit.cartography.graph.helpers import (
    remove_leading_whitespace_and_empty_lines,
)


def test_simplenode_sanity_checks():
    """
    Test creating a simple node schema with no relationships.
    """
    schema: SimpleNodeSchema = SimpleNodeSchema()
    # Assert that the unimplemented, non-abstract properties have None values.
    assert schema.extra_node_labels is None
    assert schema.sub_resource_relationship is None
    assert schema.other_relationships is None


def test_simplenode_with_subresource_sanity_checks():
    """
    Test creating a simple node schema with no relationships and ensure that the optional attributes are indeed None.
    """
    schema: SimpleNodeWithSubResourceSchema = SimpleNodeWithSubResourceSchema()
    # Assert that the unimplemented, non-abstract properties have None values.
    assert schema.extra_node_labels is None
    assert schema.other_relationships is None


def test_build_ingestion_query_with_sub_resource():
    """
    Test creating a simple node schema with a sub resource relationship.
    """
    module_version = _get_cartography_version()
    module_name = _get_module_from_schema(SimpleNodeWithSubResourceSchema())

    # Act
    query = build_ingestion_query(SimpleNodeWithSubResourceSchema())

    expected = f"""
        UNWIND $DictList AS item
            MERGE (i:SimpleNode{{id: item.Id}})
            ON CREATE SET i.firstseen = timestamp()
            SET
                i._module_name = "{module_name}",
                i._module_version = "{module_version}",
                i.lastupdated = $lastupdated,
                i.property1 = item.property1,
                i.property2 = item.property2

            WITH i, item
            CALL {{
                WITH i, item
                OPTIONAL MATCH (j:SubResource{{id: $sub_resource_id}})
                WITH i, item, j WHERE j IS NOT NULL
                MERGE (i)<-[r:RELATIONSHIP_LABEL]-(j)
                ON CREATE SET r.firstseen = timestamp()
                SET
                    r._module_name = "{module_name}",
                    r._module_version = "{module_version}",
                    r.lastupdated = $lastupdated
            }}
    """

    # Assert: compare query outputs while ignoring leading whitespace.
    actual_query = remove_leading_whitespace_and_empty_lines(query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query


def test_build_ingestion_query_case_insensitive_match():
    module_version = _get_cartography_version()
    module_name = _get_module_from_schema(FakeEmpSchema())

    query = build_ingestion_query(FakeEmpSchema())

    expected = f"""
        UNWIND $DictList AS item
            MERGE (i:FakeEmployee{{id: item.id}})
            ON CREATE SET i.firstseen = timestamp()
            SET
                i._module_name = "{module_name}",
                i._module_version = "{module_version}",
                i.lastupdated = $lastupdated,
                i.email = item.email,
                i.github_username = item.github_username

            WITH i, item
            CALL {{
                WITH i, item
                OPTIONAL MATCH (n0:GitHubUser)
                WHERE
                    toLower(n0.username) = toLower(item.github_username)
                WITH i, item, n0 WHERE n0 IS NOT NULL
                MERGE (i)-[r0:IDENTITY_GITHUB]->(n0)
                ON CREATE SET r0.firstseen = timestamp()
                SET
                    r0._module_name = "{module_name}",
                    r0._module_version = "{module_version}",
                    r0.lastupdated = $lastupdated
            }}
    """

    # Assert: compare query outputs while ignoring leading whitespace.
    actual_query = remove_leading_whitespace_and_empty_lines(query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query


def test_build_ingestion_query_fuzzy_case_insensitive():
    module_version = _get_cartography_version()
    module_name = _get_module_from_schema(FakeEmp2Schema())

    query = build_ingestion_query(FakeEmp2Schema())

    expected = f"""
        UNWIND $DictList AS item
            MERGE (i:FakeEmployee2{{id: item.id}})
            ON CREATE SET i.firstseen = timestamp()
            SET
                i._module_name = "{module_name}",
                i._module_version = "{module_version}",
                i.lastupdated = $lastupdated,
                i.email = item.email,
                i.github_username = item.github_username

        WITH i, item
        CALL {{
            WITH i, item
            OPTIONAL MATCH (n0:GitHubUser)
            WHERE
                toLower(n0.username) CONTAINS toLower(item.github_username)
            WITH i, item, n0 WHERE n0 IS NOT NULL
            MERGE (i)-[r0:IDENTITY_GITHUB]->(n0)
            ON CREATE SET r0.firstseen = timestamp()
            SET
                r0._module_name = "{module_name}",
                r0._module_version = "{module_version}",
                r0.lastupdated = $lastupdated
        }}
    """

    # Assert: compare query outputs while ignoring leading whitespace.
    actual_query = remove_leading_whitespace_and_empty_lines(query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query
