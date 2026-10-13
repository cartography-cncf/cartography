from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.api_tokens
from cartography.intel.okta.common import OktaApiError
from tests.data.okta.api_tokens import API_TOKENS
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
        MERGE (org)-[:RESOURCE]->(:OktaUser:UserAccount {id: '00u-svc-siem', lastupdated: $update_tag})
        MERGE (org)-[:RESOURCE]->(:OktaUser:UserAccount {id: '00u-alice', lastupdated: $update_tag})
        MERGE (org)-[:RESOURCE]->(:OktaNetworkZone {id: 'nzo-corp', lastupdated: $update_tag})
        MERGE (org)-[:RESOURCE]->(:OktaNetworkZone {id: 'nzo-tor', lastupdated: $update_tag})
        MERGE (org)-[:RESOURCE]->(stale:OktaApiToken {id: 'stale-token'})
        SET stale.lastupdated = 1
        """,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.okta.api_tokens,
    "_get_okta_api_tokens",
    new_callable=AsyncMock,
)
def test_sync_okta_api_tokens(mock_get_tokens, neo4j_session) -> None:
    # Arrange
    _seed_graph(neo4j_session)
    mock_get_tokens.return_value = API_TOKENS

    # Act
    cartography.intel.okta.api_tokens.sync_okta_api_tokens(
        MagicMock(),
        neo4j_session,
        _common_job_parameters(),
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "OktaApiToken",
        ["id", "name", "network_connection"],
    ) == {
        ("00T-zone-restricted", "SIEM integration", "ZONE"),
        ("00T-anywhere", "Legacy script", "ANYWHERE"),
        ("00T-no-network", "Older token without a network condition", None),
    }
    assert check_rels(
        neo4j_session,
        "OktaApiToken",
        "id",
        "OktaUser",
        "id",
        "OWNED_BY",
    ) == {
        ("00T-zone-restricted", "00u-svc-siem"),
        ("00T-anywhere", "00u-alice"),
        ("00T-no-network", "00u-alice"),
    }
    assert check_rels(
        neo4j_session,
        "OktaApiToken",
        "id",
        "OktaNetworkZone",
        "id",
        "ALLOWED_FROM",
    ) == {("00T-zone-restricted", "nzo-corp")}
    assert check_rels(
        neo4j_session,
        "OktaApiToken",
        "id",
        "OktaNetworkZone",
        "id",
        "BLOCKED_FROM",
    ) == {("00T-zone-restricted", "nzo-tor")}
    assert check_rels(
        neo4j_session,
        "OktaOrganization",
        "id",
        "OktaApiToken",
        "id",
        "RESOURCE",
    ) == {
        (TEST_ORG_ID, "00T-zone-restricted"),
        (TEST_ORG_ID, "00T-anywhere"),
        (TEST_ORG_ID, "00T-no-network"),
    }
    # Semantic APIKey label and ontology fields.
    record = neo4j_session.run(
        """
        MATCH (k:APIKey {id: '00T-zone-restricted'})-[:OWNED_BY]->(:UserAccount)
        RETURN k._ont_name AS name, k._ont_expires_at AS expires_at,
               k._ont_source AS source
        """,
    ).single()
    assert record["name"] == "SIEM integration"
    assert record["expires_at"] == "2026-10-30T00:00:00.000Z"
    assert record["source"] == "okta"


@patch.object(
    cartography.intel.okta.api_tokens,
    "_get_okta_api_tokens",
    new_callable=AsyncMock,
)
def test_sync_okta_api_tokens_skips_when_scope_missing(
    mock_get_tokens,
    neo4j_session,
) -> None:
    # Arrange
    _seed_graph(neo4j_session)
    mock_get_tokens.side_effect = OktaApiError(
        "/api/v1/api-tokens",
        SimpleNamespace(error_code="E0000006"),
    )

    # Act
    cartography.intel.okta.api_tokens.sync_okta_api_tokens(
        MagicMock(),
        neo4j_session,
        _common_job_parameters(),
    )

    # Assert
    assert check_nodes(neo4j_session, "OktaApiToken", ["id"]) == {("stale-token",)}
