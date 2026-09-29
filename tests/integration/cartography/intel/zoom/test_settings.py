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
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.settings import sync
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


def test_ingestion_batches_orphans_without_deleting_current_denied_settings(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    client = MagicMock(spec=ZoomClient)
    client.session = MagicMock()
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
    # Seed an orphan backlog left after user/group removal; no provider calls or
    # internal cleanup mocks are needed to create this prerequisite graph state.
    load(
        neo4j_session,
        ZoomSecuritySettingsSchema(),
        [
            {
                "id": f"account-one:settings:{scope}:absent-{i}:configured",
                "scope_type": scope,
                "scope_id": f"absent-{i}",
                "kind": "configured",
            }
            for scope in ("user", "group")
            for i in range(1001)
        ],
        ACCOUNT_ID="account-one",
        lastupdated=1,
    )
    # Authoritative owner removal also deletes orphan settings written with the
    # current tag, rather than retaining them because they look freshly updated.
    load(
        neo4j_session,
        ZoomSecuritySettingsSchema(),
        [
            {
                "id": f"account-one:settings:{scope}:absent-current-tag:configured",
                "scope_type": scope,
                "scope_id": "absent-current-tag",
                "kind": "configured",
            }
            for scope in ("user", "group")
        ],
        ACCOUNT_ID="account-one",
        lastupdated=2,
    )
    deny_current_user = True
    configs[0].update_tag = 2

    # Act
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
        assert current[node_id] == properties
    assert (
        current["account-one:settings:group:current-group:configured"]["lastupdated"]
        == 2
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
