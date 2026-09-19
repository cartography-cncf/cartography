from copy import deepcopy
from unittest.mock import MagicMock

import pytest
import requests

from cartography.intel.ontology.users import sync as sync_ontology_users
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.users import sync
from tests.data.zoom.users import USERS_BY_STATUS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def client_for(users_by_status):
    client = MagicMock(spec=ZoomClient)
    client.get_users_page.side_effect = lambda params: {
        "users": users_by_status[params["status"]]
    }
    return client


def test_sync_users_ontology_and_account_scoped_cleanup(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    initial = client_for(USERS_BY_STATUS)

    # Act
    sync(neo4j_session, initial, "account-a", 1)
    sync(neo4j_session, initial, "account-b", 1)
    sync_ontology_users(neo4j_session, ["zoom"], 1, {"UPDATE_TAG": 1})

    # Assert
    assert check_nodes(
        neo4j_session, "ZoomAccount", ["id", "_ont_source", "_ont_name"]
    ) == {
        ("account-a", "zoom", "account-a"),
        ("account-b", "zoom", "account-b"),
    }
    assert check_nodes(
        neo4j_session,
        "ZoomUser",
        ["email", "_ont_email", "_ont_active", "_ont_source", "plan_type"],
    ) == {
        ("alice@example.com", "alice@example.com", True, "zoom", "Licensed"),
        ("bob@example.com", "bob@example.com", False, "zoom", "Basic"),
        ("pending@example.com", "pending@example.com", False, "zoom", "Licensed"),
    }
    expected = {
        (account, f"{account}:{user}")
        for account in ("account-a", "account-b")
        for user in ("user:user-1", "user:user-2", "pending:pending@example.com")
    }
    assert (
        check_rels(neo4j_session, "ZoomAccount", "id", "ZoomUser", "id", "RESOURCE")
        == expected
    )
    assert check_rels(
        neo4j_session, "User", "email", "ZoomUser", "id", "HAS_ACCOUNT"
    ) == {
        (email, f"{account}:{user}")
        for account in ("account-a", "account-b")
        for email, user in (
            ("alice@example.com", "user:user-1"),
            ("bob@example.com", "user:user-2"),
            ("pending@example.com", "pending:pending@example.com"),
        )
    }
    alice = neo4j_session.run(
        "MATCH (u:ZoomUser {id: 'account-a:user:user-1'}) RETURN u"
    ).single()["u"]
    assert alice["role_id"] == "role-1"
    assert alice["group_ids"] == ["group-1"]
    assert alice["login_types"] == [101]

    # Arrange: activate the invitation with different email casing, remove another user.
    updated = deepcopy(USERS_BY_STATUS)
    updated["active"].append(
        {"id": "user-3", "email": "PENDING@example.com", "type": 2}
    )
    updated["pending"] = []
    updated["inactive"] = []

    # Act
    sync(neo4j_session, client_for(updated), "account-a", 2)
    sync_ontology_users(neo4j_session, ["zoom"], 2, {"UPDATE_TAG": 2})

    # Assert: stale users and invitations disappear only from the successful account.
    assert check_nodes(neo4j_session, "ZoomUser", ["id", "lastupdated"]) == {
        ("account-a:user:user-1", 2),
        ("account-a:user:user-3", 2),
        ("account-b:user:user-1", 1),
        ("account-b:user:user-2", 1),
        ("account-b:pending:pending@example.com", 1),
    }
    assert check_rels(
        neo4j_session, "ZoomAccount", "id", "ZoomUser", "id", "RESOURCE"
    ) == (
        expected
        - {
            ("account-a", "account-a:user:user-2"),
            ("account-a", "account-a:pending:pending@example.com"),
        }
    ) | {
        ("account-a", "account-a:user:user-3")
    }
    assert ("pending@example.com", "account-a:user:user-3") in check_rels(
        neo4j_session, "User", "email", "ZoomUser", "id", "HAS_ACCOUNT"
    )


def test_later_status_failure_preserves_entire_prior_snapshot(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    sync(neo4j_session, client_for(USERS_BY_STATUS), "account-a", 1)
    failing = MagicMock(spec=ZoomClient)
    failing.get_users_page.side_effect = [
        {"users": []},
        requests.HTTPError("rate limited"),
    ]

    # Act and assert
    with pytest.raises(requests.HTTPError):
        sync(neo4j_session, failing, "account-a", 2)
    assert check_nodes(neo4j_session, "ZoomUser", ["id", "lastupdated"]) == {
        ("account-a:user:user-1", 1),
        ("account-a:user:user-2", 1),
        ("account-a:pending:pending@example.com", 1),
    }
    assert check_nodes(neo4j_session, "ZoomAccount", ["id", "lastupdated"]) == {
        ("account-a", 1)
    }
    assert check_rels(
        neo4j_session, "ZoomAccount", "id", "ZoomUser", "id", "RESOURCE"
    ) == {
        ("account-a", "account-a:user:user-1"),
        ("account-a", "account-a:user:user-2"),
        ("account-a", "account-a:pending:pending@example.com"),
    }

    # Act: a complete empty inventory is authoritative.
    sync(
        neo4j_session,
        client_for({status: [] for status in USERS_BY_STATUS}),
        "account-a",
        3,
    )

    # Assert
    assert check_nodes(neo4j_session, "ZoomUser", ["id"]) == set()
