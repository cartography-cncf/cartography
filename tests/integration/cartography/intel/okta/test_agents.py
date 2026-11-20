from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.agents
from cartography.intel.okta.common import OktaApiError
from tests.data.okta.agent_pools import AGENT_POOLS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789


def _common_job_parameters() -> dict[str, int | str]:
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OKTA_ORG_ID": TEST_ORG_ID,
    }


def _seed_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (org:OktaOrganization {id: $org_id})
        SET org.lastupdated = $update_tag
        MERGE (org)-[:RESOURCE]->(pool:OktaAgentPool {id: 'stale-pool'})
        SET pool.lastupdated = 1
        MERGE (org)-[:RESOURCE]->(agent:OktaAgent {id: 'stale-agent'})
        SET agent.lastupdated = 1
        """,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.okta.agents,
    "_get_okta_agent_pools",
    new_callable=AsyncMock,
)
def test_sync_okta_agent_pools(mock_get_agent_pools, neo4j_session) -> None:
    # Arrange
    _seed_graph(neo4j_session)
    mock_get_agent_pools.return_value = AGENT_POOLS

    # Act
    synced = cartography.intel.okta.agents.sync_okta_agent_pools(
        MagicMock(),
        neo4j_session,
        _common_job_parameters(),
    )

    # Assert
    assert synced is True
    assert check_nodes(
        neo4j_session,
        "OktaAgentPool",
        ["id", "type", "operational_status"],
    ) == {
        ("pool-ldap", "LDAP", "DEGRADED"),
        ("pool-radius", "Radius", "OPERATIONAL"),
    }
    assert check_nodes(
        neo4j_session,
        "OktaAgent",
        ["id", "name", "type", "version", "is_latest_ga_version"],
    ) == {
        ("agent-ldap-old", "ldap-01.example.com", "LDAP", "5.26.2", False),
        ("agent-ldap-new", "ldap-02.example.com", "LDAP", "5.26.3", True),
    }
    assert check_rels(
        neo4j_session,
        "OktaOrganization",
        "id",
        "OktaAgentPool",
        "id",
        "RESOURCE",
    ) == {(TEST_ORG_ID, "pool-ldap"), (TEST_ORG_ID, "pool-radius")}
    assert check_rels(
        neo4j_session,
        "OktaOrganization",
        "id",
        "OktaAgent",
        "id",
        "RESOURCE",
    ) == {(TEST_ORG_ID, "agent-ldap-old"), (TEST_ORG_ID, "agent-ldap-new")}
    assert check_rels(
        neo4j_session,
        "OktaAgentPool",
        "id",
        "OktaAgent",
        "id",
        "HAS_AGENT",
    ) == {("pool-ldap", "agent-ldap-old"), ("pool-ldap", "agent-ldap-new")}
    outdated = neo4j_session.run(
        """
        MATCH (a:OktaAgent)
        WHERE a.type IN ['LDAP', 'OPP', 'Radius'] AND NOT a.is_latest_ga_version
        RETURN a.name AS name, a.last_connection.year AS year
        """,
    ).data()
    assert outdated == [{"name": "ldap-01.example.com", "year": 2025}]


@patch.object(
    cartography.intel.okta.agents,
    "_get_okta_agent_pools",
    new_callable=AsyncMock,
)
def test_sync_okta_agent_pools_skips_when_scope_missing(
    mock_get_agent_pools,
    neo4j_session,
) -> None:
    # Arrange
    _seed_graph(neo4j_session)
    mock_get_agent_pools.side_effect = OktaApiError(
        "/api/v1/agentPools",
        SimpleNamespace(error_code="E0000006"),
    )

    # Act
    synced = cartography.intel.okta.agents.sync_okta_agent_pools(
        MagicMock(),
        neo4j_session,
        _common_job_parameters(),
    )

    # Assert
    assert synced is False
    assert check_nodes(neo4j_session, "OktaAgentPool", ["id"]) == {("stale-pool",)}
    assert check_nodes(neo4j_session, "OktaAgent", ["id"]) == {("stale-agent",)}
