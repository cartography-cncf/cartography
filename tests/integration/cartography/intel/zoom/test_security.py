from collections.abc import Iterator
from copy import deepcopy
from typing import Any
from unittest.mock import MagicMock

import neo4j
import pytest
import requests

from cartography.client.core.tx import load
from cartography.intel.zoom import access
from cartography.intel.zoom import apps
from cartography.intel.zoom import client_versions
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.util import optional_call
from cartography.models.zoom.account import ZoomAccountSchema
from cartography.models.zoom.user import ZoomUserSchema
from tests.data.zoom.security import APP
from tests.data.zoom.security import APP_DETAIL
from tests.data.zoom.security import CLIENT_VERSIONS
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

    def get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if path == "/roles":
            return {"roles": deepcopy(ROLES)}
        if path == "/roles/2":
            return deepcopy(ROLE_DETAIL)
        if path == "/marketplace/apps/app-1":
            return deepcopy(APP_DETAIL)
        if path == "/metrics/client_versions":
            return deepcopy(CLIENT_VERSIONS)
        raise AssertionError(path)

    def pages(
        path: str, key: str, params: dict[str, Any] | None = None, page_size: int = 300
    ) -> list[dict[str, Any]]:
        if path == "/groups":
            return deepcopy(GROUPS)
        if path == "/marketplace/apps":
            return [deepcopy(APP)]
        raise AssertionError(path)

    client.get.side_effect = get
    client.get_paginated.side_effect = pages
    return client


def seed(session: neo4j.Session, account: str) -> list[dict[str, Any]]:
    users = [{**u, "id": u["id"].replace("account-a", account)} for u in USERS]
    load(session, ZoomAccountSchema(), [{"id": account}], lastupdated=1)
    load(session, ZoomUserSchema(), users, ACCOUNT_ID=account, lastupdated=1)
    return users


def test_access_apps_client_versions_and_scoped_cleanup(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    client = client_for()
    users_a = seed(neo4j_session, "account-a")
    users_b = seed(neo4j_session, "account-b")
    # Act
    for account, users in (("account-a", users_a), ("account-b", users_b)):
        access.sync_groups(neo4j_session, client, account, 1, users)
        access.sync_roles(neo4j_session, client, account, 1, users)
        apps.sync(neo4j_session, client, account, 1)
        client_versions.sync(neo4j_session, client, account, 1)
    # Assert
    assert check_rels(
        neo4j_session, "ZoomUser", "id", "ZoomRole", "id", "HAS_ROLE"
    ) == {(f"{a}:user:user-1", f"{a}:role:2") for a in ("account-a", "account-b")}
    assert check_rels(
        neo4j_session, "ZoomUser", "id", "ZoomGroup", "id", "MEMBER_OF"
    ) == {
        (f"{a}:user:user-1", f"{a}:group:group-1") for a in ("account-a", "account-b")
    }
    assert check_nodes(
        neo4j_session, "ZoomApp", ["installed", "approved", "approval_required"]
    ) == {(True, True, True)}
    assert check_nodes(
        neo4j_session, "ZoomRolePrivilege", ["privilege", "restricted_to_groups"]
    ) == {("User:Read", True)}
    assert (
        len(
            check_rels(
                neo4j_session, "ZoomRolePrivilege", "id", "ZoomGroup", "id", "SCOPED_TO"
            )
        )
        == 2
    )
    assert check_nodes(neo4j_session, "ZoomApp", ["developer_type"]) == {
        ("THIRD_PARTY",)
    }
    assert check_nodes(
        neo4j_session, "ZoomClientVersion", ["id", "client_version", "total_count"]
    ) == {
        (f"{a}:client_version:{version}", version, count)
        for a in ("account-a", "account-b")
        for version, count in (("mac_6.1.0", 3), ("win_6.0.0", 1))
    }
    assert check_rels(
        neo4j_session, "ZoomAccount", "id", "ZoomClientVersion", "id", "RESOURCE"
    ) == {
        (a, f"{a}:client_version:{version}")
        for a in ("account-a", "account-b")
        for version in ("mac_6.1.0", "win_6.0.0")
    }
    # Act: repeat snapshot updates existing identities.
    apps.sync(neo4j_session, client, "account-a", 2)
    # Assert
    assert len(check_nodes(neo4j_session, "ZoomApp", ["id"]) or set()) == 2
    # Arrange: complete empty reads only for account A.
    client.get_paginated.return_value = []
    client.get_paginated.side_effect = None
    client.get.side_effect = None
    client.get.return_value = {"roles": [], "client_versions": []}
    # Act
    access.sync_groups(neo4j_session, client, "account-a", 3, users_a)
    access.sync_roles(neo4j_session, client, "account-a", 3, users_a)
    apps.sync(neo4j_session, client, "account-a", 3)
    client_versions.sync(neo4j_session, client, "account-a", 3)
    # Assert
    for label in (
        "ZoomRole",
        "ZoomRolePrivilege",
        "ZoomGroup",
        "ZoomApp",
        "ZoomClientVersion",
    ):
        assert check_nodes(neo4j_session, label, ["account_id"]) == {("account-b",)}


def test_deleted_app_detail_omits_only_that_app(neo4j_session: neo4j.Session) -> None:
    # Arrange
    seed(neo4j_session, "account-a")
    client = client_for()
    other = {**APP, "app_id": "app-2", "app_name": "Other"}
    client.get_paginated.side_effect = lambda path, key, params=None: [
        deepcopy(APP),
        deepcopy(other),
    ]
    healthy = client.get.side_effect
    client.get.side_effect = lambda path, params=None: (
        {**APP_DETAIL, "app_id": "app-2"}
        if path == "/marketplace/apps/app-2"
        else healthy(path, params)
    )
    apps.sync(neo4j_session, client, "account-a", 1)
    missing = requests.Response()
    missing.status_code = 404
    missing._content = b'{"code": 1401, "message": "APP ID does not exist"}'

    def get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if path == "/marketplace/apps/app-1":
            raise requests.HTTPError(response=missing)
        return {**APP_DETAIL, "app_id": "app-2"}

    client.get.side_effect = get

    # Act: app-1 was deleted between the list and detail reads.
    apps.sync(neo4j_session, client, "account-a", 2)

    # Assert
    assert check_nodes(neo4j_session, "ZoomApp", ["id", "lastupdated"]) == {
        ("account-a:app:app-2", 2)
    }


def test_denied_detail_preserves_existing_apps(neo4j_session: neo4j.Session) -> None:
    # Arrange
    seed(neo4j_session, "account-a")
    client = client_for()
    apps.sync(neo4j_session, client, "account-a", 1)
    response = requests.Response()
    response.status_code = 403
    client.get.side_effect = requests.HTTPError(response=response)
    # Act
    optional_call("apps", lambda: apps.sync(neo4j_session, client, "account-a", 2))
    # Assert
    assert check_nodes(neo4j_session, "ZoomApp", ["id", "lastupdated"]) == {
        ("account-a:app:app-1", 1)
    }


@pytest.mark.parametrize(  # type: ignore[misc]
    "scope_fields,expected_scopes",
    [({}, None), ({"app_scopes": []}, [])],
)
def test_app_resync_clears_unknown_metadata_without_conflating_empty_scopes(
    neo4j_session: neo4j.Session,
    scope_fields: dict[str, list[str]],
    expected_scopes: list[str] | None,
) -> None:
    # Arrange
    seed(neo4j_session, "account-a")
    client = client_for()
    apps.sync(neo4j_session, client, "account-a", 1)
    client.get_paginated.side_effect = None
    client.get_paginated.return_value = [{**APP, "approval_info": None}]
    client.get.side_effect = None
    client.get.return_value = {
        **{key: value for key, value in APP_DETAIL.items() if key != "app_scopes"},
        **scope_fields,
    }

    # Act
    apps.sync(neo4j_session, client, "account-a", 2)

    # Assert
    assert check_nodes(
        neo4j_session,
        "ZoomApp",
        [
            "id",
            "lastupdated",
            "installed",
            "approved",
            "approval_type",
            "approval_required",
        ],
    ) == {("account-a:app:app-1", 2, True, True, None, None)}
    # check_nodes returns a set and cannot represent list-valued properties.
    scopes = neo4j_session.run(
        "MATCH (n:ZoomApp {id: $id}) RETURN n.app_scopes AS scopes",
        id="account-a:app:app-1",
    ).single()["scopes"]
    assert scopes == expected_scopes
    assert check_rels(
        neo4j_session, "ZoomAccount", "id", "ZoomApp", "id", "RESOURCE"
    ) == {("account-a", "account-a:app:app-1")}
