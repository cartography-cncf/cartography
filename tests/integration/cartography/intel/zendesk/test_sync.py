from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

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
    assert check_rels(
        neo4j_session,
        "ZendeskAPIToken",
        "id",
        "ZendeskUser",
        "id",
        "OWNED_BY",
    ) == {("acme:201", "acme:102")}
    # Assignees absent from the staff inventory keep their ID without OWNED_BY.
    assert check_nodes(
        neo4j_session, "ZendeskAPIToken", ["id", "assigned_user_id"]
    ) == {
        ("acme:201", 102),
        ("acme:202", None),
        ("acme:203", 103),
    }
    row = neo4j_session.run(
        "MATCH (t:ZendeskAPIToken {id: 'acme:201'}) RETURN properties(t) AS properties",
    ).single()
    assert row["properties"]["assigned_user_id"] == 102
    assert row["properties"]["last_used"] == "2026-01-02T00:00:00Z"
    assert row["properties"]["description"] == "Legacy integration"
    assert row["properties"]["_ont_source"] == "zendesk"
    assert row["properties"]["_ont_name"] == "Legacy integration"
    assert row["properties"]["_ont_created_at"] == "2025-01-01T00:00:00Z"
    assert row["properties"]["_ont_updated_at"] == "2026-01-01T00:00:00Z"
    assert row["properties"]["_ont_last_used_at"] == "2026-01-02T00:00:00Z"
    assert check_nodes(neo4j_session, "APIKey", ["id", "_ont_name"]) == {
        ("acme:201", "Legacy integration"),
        ("acme:202", "Disabled integration"),
        ("acme:203", "Former staff integration"),
    }
    assert "secret" not in str(row["properties"])
    assert (
        not {"token", "visible_token", "scopes", "expires_at"}
        & row["properties"].keys()
    )
    assert check_nodes(
        neo4j_session, "UserAccount", ["id", "_ont_source", "_ont_active"]
    ) == {
        ("acme:101", "zendesk", True),
        ("acme:102", "zendesk", False),
    }


@patch("requests.Session.get")
def test_sync_cleanup_is_tenant_scoped(mock_get, neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    mock_get.side_effect = [
        response("users", USERS),
        response("api_tokens", API_TOKENS),
        response("users", USERS),
        response("api_tokens", API_TOKENS),
    ]
    sync(neo4j_session, subdomain="acme", update_tag=1)
    sync(neo4j_session, subdomain="other", update_tag=1)
    assert check_nodes(neo4j_session, "ZendeskUser", ["id"]) == {
        ("acme:101",),
        ("acme:102",),
        ("other:101",),
        ("other:102",),
    }
    assert check_nodes(neo4j_session, "ZendeskAPIToken", ["id"]) == {
        ("acme:201",),
        ("acme:202",),
        ("acme:203",),
        ("other:201",),
        ("other:202",),
        ("other:203",),
    }
    mock_get.side_effect = [
        response("users", [USERS[1]]),
        response("api_tokens", [API_TOKENS[0]]),
    ]

    # Act
    sync(neo4j_session, subdomain="acme", update_tag=2)

    # Assert
    assert check_nodes(neo4j_session, "ZendeskUser", ["id", "lastupdated"]) == {
        ("acme:102", 2),
        ("other:101", 1),
        ("other:102", 1),
    }
    assert check_nodes(neo4j_session, "ZendeskAPIToken", ["id", "lastupdated"]) == {
        ("acme:201", 2),
        ("other:201", 1),
        ("other:202", 1),
        ("other:203", 1),
    }
    assert check_rels(
        neo4j_session, "ZendeskTenant", "id", "ZendeskUser", "id", "RESOURCE"
    ) == {
        ("acme", "acme:102"),
        ("other", "other:101"),
        ("other", "other:102"),
    }
    assert check_rels(
        neo4j_session, "ZendeskTenant", "id", "ZendeskAPIToken", "id", "RESOURCE"
    ) == {
        ("acme", "acme:201"),
        ("other", "other:201"),
        ("other", "other:202"),
        ("other", "other:203"),
    }
    assert check_rels(
        neo4j_session, "ZendeskAPIToken", "id", "ZendeskUser", "id", "OWNED_BY"
    ) == {("acme:201", "acme:102"), ("other:201", "other:102")}
    assert check_rels(
        neo4j_session, "ZendeskUser", "id", "ZendeskAPIToken", "id", "CREATED"
    ) == {("other:101", "other:201"), ("other:102", "other:202")}


@pytest.mark.parametrize("status_code", [403, 404])
@patch("requests.Session.get")
def test_token_access_error_cleanup(mock_get, neo4j_session, status_code, caplog):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    mock_get.side_effect = [
        response("users", USERS),
        response("api_tokens", API_TOKENS),
        response("users", USERS),
        response("api_tokens", API_TOKENS),
    ]
    sync(neo4j_session, subdomain="acme", update_tag=1)
    sync(neo4j_session, subdomain="other", update_tag=1)
    denied_response = requests.Response()
    denied_response.status_code = status_code
    mock_get.side_effect = [response("users", USERS), denied_response]

    # Act
    sync(neo4j_session, subdomain="acme", update_tag=2)

    # Assert
    expected_tokens = {
        ("other:201", 1),
        ("other:202", 1),
        ("other:203", 1),
    }
    if status_code == 403:
        expected_tokens |= {("acme:201", 1), ("acme:202", 1), ("acme:203", 1)}
        assert "preserving prior inventory" in caplog.text
    assert (
        check_nodes(neo4j_session, "ZendeskAPIToken", ["id", "lastupdated"])
        == expected_tokens
    )
    expected_owners = {("other:201", "other:102")}
    if status_code == 403:
        expected_owners.add(("acme:201", "acme:102"))
    assert (
        check_rels(
            neo4j_session, "ZendeskAPIToken", "id", "ZendeskUser", "id", "OWNED_BY"
        )
        == expected_owners
    )
    assert check_nodes(neo4j_session, "ZendeskUser", ["id", "lastupdated"]) == {
        ("acme:101", 2),
        ("acme:102", 2),
        ("other:101", 1),
        ("other:102", 1),
    }
