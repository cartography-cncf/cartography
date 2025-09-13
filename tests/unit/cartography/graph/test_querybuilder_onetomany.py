from cartography.graph.querybuilder import _get_cartography_version
from cartography.graph.querybuilder import _get_module_from_schema
from cartography.graph.querybuilder import build_ingestion_query
from cartography.models.aws.iam.instanceprofile import InstanceProfileSchema
from tests.unit.cartography.graph.helpers import (
    remove_leading_whitespace_and_empty_lines,
)


def test_build_ingestion_query_onetomany():
    module_version = _get_cartography_version()
    module_name = _get_module_from_schema(InstanceProfileSchema())

    # Act
    query = build_ingestion_query(InstanceProfileSchema())

    expected = f"""
    UNWIND $DictList AS item
        MERGE (i:AWSInstanceProfile{{id: item.Arn}})
        ON CREATE SET i.firstseen = timestamp()
        SET
            i._module_name = "{module_name}",
            i._module_version = "{module_version}",
            i.lastupdated = $lastupdated,
            i.arn = item.Arn,
            i.createdate = item.CreateDate,
            i.instance_profile_id = item.InstanceProfileId,
            i.instance_profile_name = item.InstanceProfileName,
            i.path = item.Path
        WITH i, item
        CALL {{
            WITH i, item
            OPTIONAL MATCH (j:AWSAccount{{id: $AWS_ID}})
            WITH i, item, j WHERE j IS NOT NULL
            MERGE (i)<-[r:RESOURCE]-(j)
            ON CREATE SET r.firstseen = timestamp()
            SET
                r._module_name = "{module_name}",
                r._module_version = "{module_version}",
                r.lastupdated = $lastupdated

            UNION
            WITH i, item
            OPTIONAL MATCH (n0:AWSRole)
            WHERE
                n0.arn IN item.Roles

            WITH i, item, n0 WHERE n0 IS NOT NULL
            MERGE (i)-[r0:ASSOCIATED_WITH]->(n0)
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
