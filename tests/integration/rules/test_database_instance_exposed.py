import pytest

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.database_instance_exposed import (
    _scaleway_datawarehouse_public_access,
)
from cartography.rules.data.rules.database_instance_exposed import (
    _scaleway_searchdb_public_access,
)
from cartography.rules.data.rules.database_instance_exposed import (
    _scaleway_serverless_sql_public_access,
)

# (fact, node label, the host column the fact returns, expected engine)
CASES = [
    (
        _scaleway_datawarehouse_public_access,
        "ScalewayDataWarehouseDeployment",
        "dw-public",
        "clickhouse",
    ),
    (
        _scaleway_searchdb_public_access,
        "ScalewaySearchDeployment",
        "search-public",
        "opensearch",
    ),
]


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


@pytest.mark.parametrize(
    ("fact", "label", "expected_host", "expected_engine"),
    CASES,
    ids=[c[1] for c in CASES],
)
def test_scaleway_data_service_public_endpoint(
    neo4j_session, fact, label, expected_host, expected_engine
):
    _reset_graph(neo4j_session)
    neo4j_session.run(
        f"""
        CREATE (prj:ScalewayProject {{id: 'proj-1'}})
        CREATE (pub:{label} {{id: 'd-public', name: '{expected_host}',
            is_public: true, version: '24.3', region: 'fr-par'}})
        CREATE (priv:{label} {{id: 'd-private', name: 'private',
            is_public: false, version: '24.3', region: 'fr-par'}})
        MERGE (prj)-[:RESOURCE]->(pub)
        MERGE (prj)-[:RESOURCE]->(priv)
        """
    )

    findings = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)

    assert [(f["id"], f["host"], f["engine"], f["region"]) for f in findings] == [
        ("d-public", expected_host, expected_engine, "fr-par")
    ]


def test_scaleway_serverless_sql_public_endpoint(neo4j_session) -> None:
    """Serverless SQL reports its connection endpoint as the host, not its name."""
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (prj:ScalewayProject {id: 'proj-1'})
        CREATE (pub:ScalewayServerlessSQLDatabase {id: 'd-public', name: 'public',
            endpoint: 'postgres://db.fr-par.scw.cloud:5432', is_public: true,
            engine_major_version: '16', region: 'fr-par'})
        CREATE (priv:ScalewayServerlessSQLDatabase {id: 'd-private', name: 'private',
            endpoint: null, is_public: false, engine_major_version: '16',
            region: 'fr-par'})
        MERGE (prj)-[:RESOURCE]->(pub)
        MERGE (prj)-[:RESOURCE]->(priv)
        """
    )

    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx, _scaleway_serverless_sql_public_access.cypher_query
    )

    assert [(f["id"], f["host"], f["engine"]) for f in findings] == [
        ("d-public", "postgres://db.fr-par.scw.cloud:5432", "postgres")
    ]
