from unittest.mock import Mock
from unittest.mock import patch

from cartography.config import Config
from cartography.intel.zendesk import start_zendesk_ingestion
from tests.data.zendesk.api_tokens import API_TOKENS
from tests.data.zendesk.users import USERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def response(key, records):
    if key == "api_tokens":
        return Mock(json=lambda: {key: records})
    return Mock(
        json=lambda: {
            key: records,
            "meta": {"has_more": False},
            "links": {"next": None},
        }
    )


def sync(neo4j_session, subdomain="acme", update_tag=1):
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        zendesk_subdomain=subdomain,
        zendesk_oauth_token="test-oauth-token",
    )
    config.update_tag = update_tag
    start_zendesk_ingestion(neo4j_session, config)


@patch("requests.Session.get")
def test_sync_inventory(mock_get, neo4j_session):
    # Arrange
    mock_get.side_effect = [
        response("users", USERS),
        response("api_tokens", API_TOKENS),
    ]

    # Act
    sync(neo4j_session, subdomain=" Acme ")

    # Assert
    assert check_nodes(neo4j_session, "ZendeskTenant", ["id", "_ont_domain"]) == {
        ("acme", "acme.zendesk.com")
    }
    assert check_nodes(
        neo4j_session, "ZendeskUser", ["id", "role", "suspended", "_ont_email"]
    ) == {
        ("acme:101", "admin", False, "alice@example.com"),
        ("acme:102", "agent", True, "bob@example.com"),
    }
    assert check_nodes(
        neo4j_session, "ZendeskAPIToken", ["id", "creator_user_id", "active"]
    ) == {
        ("acme:201", 101, True),
        ("acme:202", 102, False),
        ("acme:203", 103, True),
    }
    assert check_rels(
        neo4j_session, "ZendeskTenant", "id", "ZendeskUser", "id", "RESOURCE"
    ) == {
        ("acme", "acme:101"),
        ("acme", "acme:102"),
    }
    assert check_rels(
        neo4j_session, "ZendeskTenant", "id", "ZendeskAPIToken", "id", "RESOURCE"
    ) == {
        ("acme", "acme:201"),
        ("acme", "acme:202"),
        ("acme", "acme:203"),
    }
    assert check_rels(
        neo4j_session, "ZendeskUser", "id", "ZendeskAPIToken", "id", "CREATED"
    ) == {
        ("acme:101", "acme:201"),
        ("acme:102", "acme:202"),
    }
    row = neo4j_session.run(
        "MATCH (t:ZendeskAPIToken {id: 'acme:201'}) RETURN properties(t) AS properties",
    ).single()
    assert row["properties"]["assigned_user_id"] == 102
    assert row["properties"]["last_used"] == "2026-01-02T00:00:00Z"
    assert row["properties"]["description"] == "Legacy integration"
    assert "secret" not in str(row["properties"])
    assert (
        not {"token", "visible_token", "scopes", "expires_at"}
        & row["properties"].keys()
    )
    assert check_nodes(neo4j_session, "UserAccount", ["id", "_ont_source"]) == {
        ("acme:101", "zendesk"),
        ("acme:102", "zendesk"),
    }
