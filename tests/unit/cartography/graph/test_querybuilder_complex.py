from cartography.graph.querybuilder import _get_cartography_version
from cartography.graph.querybuilder import _get_module_from_schema
from cartography.graph.querybuilder import build_ingestion_query
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetSchema,
)
from tests.unit.cartography.graph.helpers import (
    remove_leading_whitespace_and_empty_lines,
)


def test_build_ingestion_query_complex():
    module_version = _get_cartography_version()
    module_name = _get_module_from_schema(InterestingAssetSchema())

    # Act
    query = build_ingestion_query(InterestingAssetSchema())

    expected = f"""
        UNWIND $DictList AS item
            MERGE (i:InterestingAsset{{id: item.Id}})
            ON CREATE SET i.firstseen = timestamp()
            SET
                i._module_name = "{module_name}",
                i._module_version = "{module_version}",
                i.lastupdated = $lastupdated,
                i.property1 = item.property1,
                i.property2 = item.property2,
                i:AnotherNodeLabel:YetAnotherNodeLabel

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
                    r.lastupdated = $lastupdated,
                    r.another_rel_field = item.AnotherField,
                    r.yet_another_rel_field = item.YetAnotherRelField

                UNION
                WITH i, item
                OPTIONAL MATCH (n0:HelloAsset)
                WHERE
                    n0.id = item.hello_asset_id
                WITH i, item, n0 WHERE n0 IS NOT NULL
                MERGE (i)-[r0:ASSOCIATED_WITH]->(n0)
                ON CREATE SET r0.firstseen = timestamp()
                SET
                    r0._module_name = "{module_name}",
                    r0._module_version = "{module_version}",
                    r0.lastupdated = $lastupdated

                UNION
                WITH i, item
                OPTIONAL MATCH (n1:WorldAsset)
                WHERE
                    n1.id = item.world_asset_id
                WITH i, item, n1 WHERE n1 IS NOT NULL
                MERGE (i)<-[r1:CONNECTED]-(n1)
                ON CREATE SET r1.firstseen = timestamp()
                SET
                    r1._module_name = "{module_name}",
                    r1._module_version = "{module_version}",
                    r1.lastupdated = $lastupdated
            }}
    """

    # Assert: compare query outputs while ignoring leading whitespace.
    actual_query = remove_leading_whitespace_and_empty_lines(query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query
