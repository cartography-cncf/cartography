from collections.abc import Iterator
from copy import deepcopy
from unittest.mock import MagicMock

import neo4j
import pytest

from cartography.intel.zoom import access
from cartography.intel.zoom import apps
from cartography.intel.zoom import users
from cartography.intel.zoom.client import ZoomClient
from tests.data.zoom.security import APP
from tests.data.zoom.security import APP_DETAIL
from tests.data.zoom.security import GROUPS
from tests.data.zoom.security import ROLE_DETAIL
from tests.data.zoom.security import ROLES
from tests.data.zoom.security import USERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


@pytest.fixture(autouse=True)  # type: ignore[misc]
def clean_graph(neo4j_session: neo4j.Session) -> Iterator[None]:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    try:
        yield
    finally:
        neo4j_session.run("MATCH (n) DETACH DELETE n")


def client_for() -> MagicMock:
    client = MagicMock(spec=ZoomClient)
    client.session = MagicMock()
    client.fork.return_value = client
    client.get_users_page.side_effect = lambda params: {
        "users": (
            [{**user, "id": user["zoom_id"]} for user in USERS]
            if params["status"] == "active"
            else []
        )
    }
    return client


def test_groups_and_roles_have_traversable_ontology_properties(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    client = client_for()
    client.get_paginated.return_value = deepcopy(GROUPS)
    client.get.side_effect = lambda path, params=None: {
        "/roles": {"roles": ROLES, "total_records": len(ROLES)},
        "/roles/2": ROLE_DETAIL,
    }[path]

    # Act
    for account in ("account-a", "account-b"):
        account_users = users.sync(neo4j_session, client, account, 1)
        access.sync_groups(neo4j_session, client, account, 1, account_users)
        access.sync_roles(neo4j_session, client, account, 1, account_users)

    # Assert
    assert check_nodes(
        neo4j_session, "ZoomGroup:UserGroup", ["id", "_ont_source", "_ont_name"]
    ) == {
        (f"{account}:group:group-1", "zoom", "Engineering")
        for account in ("account-a", "account-b")
    }
    assert check_nodes(
        neo4j_session,
        "ZoomRole:PermissionRole",
        ["id", "_ont_source", "_ont_name", "_ont_scope", "_ont_type"],
    ) == {
        (f"{account}:role:2", "zoom", "Member", "account", None)
        for account in ("account-a", "account-b")
    }
    assert check_rels(
        neo4j_session,
        "UserAccount",
        "id",
        "UserGroup",
        "id",
        "MEMBER_OF",
    ) == {
        (f"{account}:user:user-1", f"{account}:group:group-1")
        for account in ("account-a", "account-b")
    }
    assert check_rels(
        neo4j_session,
        "UserAccount",
        "id",
        "PermissionRole",
        "id",
        "HAS_ROLE",
    ) == {
        (f"{account}:user:user-1", f"{account}:role:2")
        for account in ("account-a", "account-b")
    }
    for label, suffix in (("UserGroup", "group:group-1"), ("PermissionRole", "role:2")):
        assert check_rels(neo4j_session, "Tenant", "id", label, "id", "RESOURCE") == {
            (account, f"{account}:{suffix}") for account in ("account-a", "account-b")
        }


def test_app_ontology_uses_marketplace_identifier_without_inferred_posture(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    client = client_for()
    client.get_paginated.return_value = [deepcopy(APP)]
    detail = deepcopy(APP_DETAIL)
    client.get.return_value = detail
    for account in ("account-a", "account-b"):
        users.sync(neo4j_session, client, account, 1)

    # Act
    apps.sync(neo4j_session, client, "account-a", 1)
    detail["app_status"] = "PUBLISHED"
    apps.sync(neo4j_session, client, "account-b", 1)

    # Assert
    assert check_nodes(
        neo4j_session,
        "ZoomApp:ThirdPartyApp",
        [
            "id",
            "_ont_source",
            "_ont_name",
            "_ont_client_id",
            "_ont_enabled",
            "_ont_protocol",
            "_ont_native_app",
        ],
    ) == {
        (f"{account}:app:app-1", "zoom", "Inventory", "app-1", None, None, None)
        for account in ("account-a", "account-b")
    }
    assert check_rels(
        neo4j_session, "Tenant", "id", "ThirdPartyApp", "id", "RESOURCE"
    ) == {(account, f"{account}:app:app-1") for account in ("account-a", "account-b")}
    assert check_nodes(neo4j_session, "ZoomApp", ["account_id", "app_status"]) == {
        ("account-a", "UNPUBLISHED"),
        ("account-b", "PUBLISHED"),
    }
