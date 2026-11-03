import json
from collections.abc import Iterator
from copy import deepcopy
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j
import pytest
import requests

from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.zoom import start_zoom_ingestion
from cartography.intel.zoom.client import RequestBudget
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.client import ZoomRequestLimitError
from cartography.intel.zoom.settings import sync
from cartography.intel.zoom.users import sync as users_sync
from cartography.models.zoom.account import ZoomAccountSchema
from cartography.models.zoom.group import ZoomGroupSchema
from cartography.models.zoom.settings import ZoomSecuritySettingsSchema
from cartography.models.zoom.user import ZoomUserSchema
from tests.data.zoom.settings import LOCKED_SETTINGS_RESPONSES
from tests.data.zoom.settings import SETTINGS_RESPONSES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


@pytest.fixture(autouse=True)  # type: ignore[misc]
def clean_graph(neo4j_session: neo4j.Session) -> Iterator[None]:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    try:
        yield
    finally:
        neo4j_session.run("MATCH (n) DETACH DELETE n")


def test_settings_preserve_denied_kind_and_isolate_accounts(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    users = [
        {"id": "account-one:user:user-one", "zoom_id": "user-one", "status": "active"}
    ]
    groups = [{"id": "group-one"}]
    configured = deepcopy(SETTINGS_RESPONSES)
    denied_group_locks = False
    client = MagicMock(spec=ZoomClient)
    client.session = MagicMock()
    client.fork.return_value = client

    def response(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        option = (params or {}).get("option", "default")
        if (
            denied_group_locks
            and path == "/groups/group-one/lock_settings"
            and option == "meeting_security"
        ):
            denied = requests.Response()
            denied.status_code = 403
            raise requests.HTTPError(response=denied)
        values = (
            LOCKED_SETTINGS_RESPONSES if path.endswith("lock_settings") else configured
        )
        return deepcopy(values[option])

    client.get.side_effect = response
    for account in ("account-one", "account-two"):
        load(neo4j_session, ZoomAccountSchema(), [{"id": account}], lastupdated=1)
        load(
            neo4j_session,
            ZoomUserSchema(),
            [{"id": f"{account}:user:user-one", "email": "user@example.com"}],
            ACCOUNT_ID=account,
            lastupdated=1,
        )
        load(
            neo4j_session,
            ZoomGroupSchema(),
            [
                {
                    "id": f"{account}:group:group-one",
                    "zoom_id": "group-one",
                    "name": "Group one",
                    "member_ids": [],
                }
            ],
            ACCOUNT_ID=account,
            lastupdated=1,
        )

    # Act
    sync(neo4j_session, client, "account-one", 1, users, groups)
    sync(neo4j_session, client, "account-two", 1, users, groups)

    # Assert
    expected_ids = {
        f"{account}:settings:{scope}:{owner}:{kind}"
        for account in ("account-one", "account-two")
        for scope, owner, kind in (
            ("account", account, "configured"),
            ("account", account, "locked"),
            ("group", "group-one", "configured"),
            ("group", "group-one", "locked"),
            ("user", "user-one", "configured"),
        )
    }
    assert check_nodes(neo4j_session, "ZoomSecuritySettings", ["id"]) == {
        (node_id,) for node_id in expected_ids
    }
    assert check_rels(
        neo4j_session, "ZoomAccount", "id", "ZoomSecuritySettings", "id", "RESOURCE"
    ) == {(node_id.split(":", 1)[0], node_id) for node_id in expected_ids}
    for scope, label, owner in (
        ("account", "ZoomAccount", None),
        ("group", "ZoomGroup", "group-one"),
        ("user", "ZoomUser", "user-one"),
    ):
        assert check_rels(
            neo4j_session, label, "id", "ZoomSecuritySettings", "id", "HAS_SETTINGS"
        ) == {
            (account if scope == "account" else f"{account}:{scope}:{owner}", node_id)
            for account in ("account-one", "account-two")
            for node_id in expected_ids
            if node_id.startswith(f"{account}:settings:{scope}:")
        }

    # Arrange
    configured["default"]["recording"]["cloud_recording"] = False
    configured["default"]["in_meeting"].pop("file_transfer")
    denied_group_locks = True

    # Act
    sync(neo4j_session, client, "account-one", 2, users, groups)

    # Assert
    assert check_nodes(neo4j_session, "ZoomSecuritySettings", ["id"]) == {
        (node_id,) for node_id in expected_ids
    }
    # Read all properties to catch accidental secret ingestion, including fields
    # outside the allowlist that an explicit check_nodes projection would omit.
    settings = {
        record["n"]["id"]: record["n"]
        for record in neo4j_session.run("MATCH (n:ZoomSecuritySettings) RETURN n")
    }
    for node_id, node in settings.items():
        if (
            node_id.startswith("account-two:")
            or node_id == "account-one:settings:group:group-one:locked"
        ):
            assert node["lastupdated"] == 1
        else:
            assert node["lastupdated"] == 2
    assert (
        settings["account-one:settings:group:group-one:locked"][
            "meeting_authentication"
        ]
        is True
    )
    for scope, owner in (
        ("account", "account-one"),
        ("group", "group-one"),
        ("user", "user-one"),
    ):
        node = settings[f"account-one:settings:{scope}:{owner}:configured"]
        assert node["cloud_recording"] is False
        assert node.get("file_transfer") is None
    assert (
        settings["account-two:settings:user:user-one:configured"]["cloud_recording"]
        is True
    )
    assert (
        settings["account-two:settings:user:user-one:configured"]["file_transfer"]
        is False
    )
    assert "synthetic-secret" not in str(settings)


def test_ingestion_removes_departed_owner_settings_after_a_complete_read(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    client = MagicMock(spec=ZoomClient)
    client.session = MagicMock()
    client.fork.return_value = client
    client.get_users_page.side_effect = lambda params: {
        "users": (
            [
                {
                    "id": "current-user",
                    "email": "current@example.com",
                    "type": 2,
                    "group_ids": ["current-group"],
                }
            ]
            if params["status"] == "active"
            else []
        ),
    }
    client.get_paginated.return_value = [
        {"id": "current-group", "name": "Current group"}
    ]
    deny_current_user = False

    def response(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if deny_current_user and path == "/users/current-user/settings":
            denied = requests.Response()
            denied.status_code = 403
            raise requests.HTTPError(response=denied)
        values = (
            LOCKED_SETTINGS_RESPONSES
            if path.endswith("lock_settings")
            else SETTINGS_RESPONSES
        )
        return deepcopy(values[(params or {}).get("option", "default")])

    client.get.side_effect = response
    configs = [
        Config(
            neo4j_uri="bolt://localhost:7687",
            zoom_account_id=account,
            zoom_client_id="synthetic-client",
            zoom_client_secret="synthetic-secret",
            zoom_sections="settings",
            update_tag=1,
        )
        for account in ("account-one", "account-two")
    ]
    with patch("cartography.intel.zoom.ZoomClient", return_value=client):
        for config in configs:
            start_zoom_ingestion(neo4j_session, config)
    expected_ids = check_nodes(neo4j_session, "ZoomSecuritySettings", ["id"])
    assert expected_ids is not None
    expected_resource_edges = check_rels(
        neo4j_session, "ZoomAccount", "id", "ZoomSecuritySettings", "id", "RESOURCE"
    )
    # Preserve the complete property maps so cleanup cannot silently alter any
    # metadata on a denied owner or another account.
    preserved = {
        record["n"]["id"]: dict(record["n"])
        for record in neo4j_session.run(
            """
            MATCH (n:ZoomSecuritySettings)
            WHERE n.account_id = 'account-two' OR n.id = 'account-one:settings:user:current-user:configured'
            RETURN n
            """,
        )
    }
    # Seed owners that have since left the account, each with a settings snapshot.
    load(
        neo4j_session,
        ZoomUserSchema(),
        [
            {"id": f"account-one:user:absent-{i}", "email": f"absent-{i}@example.com"}
            for i in range(1001)
        ],
        ACCOUNT_ID="account-one",
        lastupdated=1,
    )
    load(
        neo4j_session,
        ZoomGroupSchema(),
        [
            {
                "id": f"account-one:group:absent-{i}",
                "zoom_id": f"absent-{i}",
                "name": f"Absent {i}",
                "member_ids": [],
            }
            for i in range(1001)
        ],
        ACCOUNT_ID="account-one",
        lastupdated=1,
    )
    load(
        neo4j_session,
        ZoomSecuritySettingsSchema(),
        [
            {
                "id": f"account-one:settings:{scope}:absent-{i}:configured",
                "scope_type": scope,
                "scope_id": f"absent-{i}",
                "kind": "configured",
                f"{scope}_owner_id": f"account-one:{scope}:absent-{i}",
            }
            for scope in ("user", "group")
            for i in range(1001)
        ],
        ACCOUNT_ID="account-one",
        lastupdated=1,
    )
    departed_ids = {
        (f"account-one:settings:{scope}:absent-{i}:configured",)
        for scope in ("user", "group")
        for i in range(1001)
    }

    # Act: a denied owner makes the snapshot incomplete, so cleanup is skipped.
    deny_current_user = True
    configs[0].update_tag = 2
    with patch("cartography.intel.zoom.ZoomClient", return_value=client):
        start_zoom_ingestion(neo4j_session, configs[0])

    # Assert
    assert (
        check_nodes(neo4j_session, "ZoomSecuritySettings", ["id"])
        == expected_ids | departed_ids
    )
    current = {
        record["n"]["id"]: dict(record["n"])
        for record in neo4j_session.run("MATCH (n:ZoomSecuritySettings) RETURN n")
    }
    for node_id, properties in preserved.items():
        assert current[node_id] == properties

    # Act: a complete read removes the departed owners' settings.
    deny_current_user = False
    configs[0].update_tag = 3
    with patch("cartography.intel.zoom.ZoomClient", return_value=client):
        start_zoom_ingestion(neo4j_session, configs[0])

    # Assert
    assert check_nodes(neo4j_session, "ZoomSecuritySettings", ["id"]) == expected_ids
    assert (
        check_rels(
            neo4j_session, "ZoomAccount", "id", "ZoomSecuritySettings", "id", "RESOURCE"
        )
        == expected_resource_edges
    )
    current = {
        record["n"]["id"]: dict(record["n"])
        for record in neo4j_session.run("MATCH (n:ZoomSecuritySettings) RETURN n")
    }
    for node_id, properties in preserved.items():
        if properties["account_id"] == "account-two":
            assert current[node_id] == properties
    assert (
        current["account-one:settings:group:current-group:configured"]["lastupdated"]
        == 3
    )
    assert check_rels(
        neo4j_session, "ZoomUser", "id", "ZoomSecuritySettings", "id", "HAS_SETTINGS"
    ) == {
        (
            f"{account}:user:current-user",
            f"{account}:settings:user:current-user:configured",
        )
        for account in ("account-one", "account-two")
    }
    for label, scope in (("ZoomUser", "user"), ("ZoomGroup", "group")):
        assert check_nodes(neo4j_session, label, ["id"]) == {
            (f"{account}:{scope}:current-{scope}",)
            for account in ("account-one", "account-two")
        }
        assert check_rels(
            neo4j_session, label, "id", "ZoomSecuritySettings", "id", "HAS_SETTINGS"
        ) == {
            (
                f"{account}:{scope}:current-{scope}",
                f"{account}:settings:{scope}:current-{scope}:{kind}",
            )
            for account in ("account-one", "account-two")
            for kind in (
                ("configured",) if scope == "user" else ("configured", "locked")
            )
        }


def http_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> list[str]:
    """Serve synthetic settings at the HTTP boundary of a real ZoomClient."""
    calls: list[str] = []

    def post(self: requests.Session, url: str, **kwargs: Any) -> requests.Response:
        result = requests.Response()
        result.status_code = 200
        result._content = json.dumps(
            {"access_token": "synthetic-token", "expires_in": 3600}
        ).encode()
        return result

    def get(self: requests.Session, url: str, **kwargs: Any) -> requests.Response:
        calls.append(url)
        option = (kwargs.get("params") or {}).get("option", "default")
        values = (
            LOCKED_SETTINGS_RESPONSES
            if url.endswith("lock_settings")
            else SETTINGS_RESPONSES
        )
        result = requests.Response()
        result.status_code = 200
        result._content = json.dumps(values[option]).encode()
        return result

    monkeypatch.setattr(requests.Session, "post", post)
    monkeypatch.setattr(requests.Session, "get", get)
    return calls


def many_users(count: int) -> list[dict[str, Any]]:
    return [
        {
            "id": f"account-one:user:user-{i}",
            "zoom_id": f"user-{i}",
            "email": f"user-{i}@example.com",
            "status": "active",
        }
        for i in range(count)
    ]


def test_default_limits_cover_large_user_settings_inventory(
    neo4j_session: neo4j.Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    calls = http_settings(monkeypatch)
    users = many_users(2500)
    load(neo4j_session, ZoomAccountSchema(), [{"id": "account-one"}], lastupdated=1)
    load(
        neo4j_session, ZoomUserSchema(), users, ACCOUNT_ID="account-one", lastupdated=1
    )
    client = ZoomClient("account-one", "synthetic-client", "synthetic-secret")

    # Act
    sync(neo4j_session, client, "account-one", 1, users, None)

    # Assert: two account kinds plus four configured reads for each user.
    assert len(calls) == 7 + 4 * len(users)
    assert client.budget.remaining == 100000 - len(calls)
    records = check_nodes(neo4j_session, "ZoomSecuritySettings", ["id", "lastupdated"])
    assert records is not None
    assert len(records) == 2 + len(users)
    assert {tag for _, tag in records} == {1}


def test_request_limit_preserves_unread_settings_and_users_still_fail(
    neo4j_session: neo4j.Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    calls = http_settings(monkeypatch)
    users = many_users(30)
    load(neo4j_session, ZoomAccountSchema(), [{"id": "account-one"}], lastupdated=1)
    load(
        neo4j_session, ZoomUserSchema(), users, ACCOUNT_ID="account-one", lastupdated=1
    )
    sync(
        neo4j_session,
        ZoomClient("account-one", "synthetic-client", "synthetic-secret"),
        "account-one",
        1,
        users,
        None,
    )
    before = {
        record["n"]["id"]: dict(record["n"])
        for record in neo4j_session.run("MATCH (n:ZoomSecuritySettings) RETURN n")
    }
    calls.clear()
    limited = ZoomClient(
        "account-one", "synthetic-client", "synthetic-secret", RequestBudget(40)
    )

    # Act: the limit is reached partway through the owner reads.
    sync(neo4j_session, limited, "account-one", 2, users, None)

    # Assert: no request is attempted past the limit, and every snapshot is
    # either completely refreshed or left exactly as it was.
    assert len(calls) == 40
    after = {
        record["n"]["id"]: dict(record["n"])
        for record in neo4j_session.run("MATCH (n:ZoomSecuritySettings) RETURN n")
    }
    assert set(after) == set(before)
    refreshed = {node_id for node_id, node in after.items() if node["lastupdated"] == 2}
    assert 0 < len(refreshed) < len(after)
    for node_id in set(after) - refreshed:
        assert after[node_id] == before[node_id]

    # Act and assert: the required user inventory still fails on the limit.
    with pytest.raises(ZoomRequestLimitError):
        users_sync(neo4j_session, limited, "account-one", 3)
