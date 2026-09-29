from collections.abc import Iterator
from copy import deepcopy
from typing import Any
from unittest.mock import MagicMock

import neo4j
import pytest
import requests

from cartography.client.core.tx import load
from cartography.intel.zoom import access
from cartography.intel.zoom import activity
from cartography.intel.zoom import apps
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.util import optional_call
from cartography.models.zoom.account import ZoomAccountSchema
from cartography.models.zoom.user import ZoomUserSchema
from tests.data.zoom.security import APP
from tests.data.zoom.security import APP_DETAIL
from tests.data.zoom.security import GROUPS
from tests.data.zoom.security import PARTICIPANT
from tests.data.zoom.security import ROLE_DETAIL
from tests.data.zoom.security import ROLES
from tests.data.zoom.security import SESSION
from tests.data.zoom.security import SIGNIN
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
        raise AssertionError(path)

    def pages(
        path: str, key: str, params: dict[str, Any] | None = None, page_size: int = 300
    ) -> list[dict[str, Any]]:
        if path == "/groups":
            return deepcopy(GROUPS)
        if path == "/marketplace/apps":
            return [deepcopy(APP)]
        if path == "/report/activities":
            return [deepcopy(SIGNIN)]
        if path in ("/report/operationlogs", "/report/meeting_activities"):
            return []
        if path == "/metrics/meetings":
            return [deepcopy(SESSION)] if params and params["type"] == "pastOne" else []
        if path == "/metrics/meetings/%252Fsession%252F%252Fone/participants":
            return [deepcopy(PARTICIPANT)]
        raise AssertionError(path)

    client.get.side_effect = get
    client.get_paginated.side_effect = pages
    return client


def seed(session: neo4j.Session, account: str) -> list[dict[str, Any]]:
    users = [{**u, "id": u["id"].replace("account-a", account)} for u in USERS]
    load(session, ZoomAccountSchema(), [{"id": account}], lastupdated=1)
    load(session, ZoomUserSchema(), users, ACCOUNT_ID=account, lastupdated=1)
    return users


def test_access_apps_activity_relationships_and_scoped_cleanup(
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
        activity.sync_reports(neo4j_session, client, account, 1, users, 1)
        activity.sync_dashboard(neo4j_session, client, account, 1, users, 1)
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
    assert (
        len(
            check_rels(
                neo4j_session,
                "ZoomActivityEvent",
                "id",
                "ZoomUser",
                "id",
                "PERFORMED_BY",
            )
        )
        == 2
    )
    assert (
        len(
            check_rels(
                neo4j_session,
                "ZoomMeetingParticipant",
                "id",
                "ZoomMeetingSession",
                "id",
                "IN_MEETING",
            )
        )
        == 2
    )
    assert check_nodes(
        neo4j_session, "ZoomMeetingParticipant", ["device", "client_version"]
    ) == {("Mac", "6.1.0")}
    # Act: repeat snapshot updates existing identities.
    apps.sync(neo4j_session, client, "account-a", 2)
    activity.sync_dashboard(neo4j_session, client, "account-a", 2, users_a, 1)
    # Assert
    assert len(check_nodes(neo4j_session, "ZoomApp", ["id"]) or set()) == 2
    assert (
        len(check_nodes(neo4j_session, "ZoomMeetingParticipant", ["id"]) or set()) == 2
    )
    # Arrange: complete empty reads only for account A.
    client.get_paginated.return_value = []
    client.get_paginated.side_effect = None
    client.get.side_effect = None
    client.get.return_value = {"roles": []}
    # Act
    access.sync_groups(neo4j_session, client, "account-a", 3, users_a)
    access.sync_roles(neo4j_session, client, "account-a", 3, users_a)
    apps.sync(neo4j_session, client, "account-a", 3)
    activity.sync_reports(neo4j_session, client, "account-a", 3, users_a, 1)
    activity.sync_dashboard(neo4j_session, client, "account-a", 3, users_a, 1)
    # Assert
    for label in (
        "ZoomRole",
        "ZoomRolePrivilege",
        "ZoomGroup",
        "ZoomApp",
        "ZoomActivityEvent",
        "ZoomMeetingSession",
        "ZoomMeetingParticipant",
    ):
        assert check_nodes(neo4j_session, label, ["account_id"]) == {("account-b",)}


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


def test_report_cleanup_batches_preserve_denied_sources_and_other_accounts(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    users_a = seed(neo4j_session, "account-a")
    users_b = seed(neo4j_session, "account-b")
    client = MagicMock(spec=ZoomClient)
    signin_rows = [{**SIGNIN, "version": f"6.1.{i}"} for i in range(1001)]
    operations = [
        {"operator": USERS[0]["email"], "time": SIGNIN["time"], "action": "Update"}
    ]
    audit = [
        {
            "operator_email": USERS[0]["email"],
            "activity_time": SIGNIN["time"],
            "activity_category": "Meeting Started",
        }
    ]
    deny_operations = False

    def pages(
        path: str,
        key: str,
        params: dict[str, Any] | None = None,
        page_size: int = 300,
    ) -> list[dict[str, Any]]:
        if path == "/report/activities":
            return signin_rows
        if path == "/report/operationlogs":
            if deny_operations:
                response = requests.Response()
                response.status_code = 403
                raise requests.HTTPError(response=response)
            return operations
        if path == "/report/meeting_activities":
            return audit
        raise AssertionError(path)

    client.get_paginated.side_effect = pages
    activity.sync_reports(neo4j_session, client, "account-a", 1, users_a, 1)
    signin_rows = [SIGNIN]
    activity.sync_reports(neo4j_session, client, "account-b", 1, users_b, 1)
    signin_rows = [{**SIGNIN, "version": "6.2.0"}]
    audit = []
    deny_operations = True

    # Act
    activity.sync_reports(neo4j_session, client, "account-a", 2, users_a, 1)

    # Assert
    assert check_nodes(
        neo4j_session, "ZoomActivityEvent", ["account_id", "source", "lastupdated"]
    ) == {
        ("account-a", "signins", 2),
        ("account-a", "operations", 1),
        ("account-b", "signins", 1),
        ("account-b", "operations", 1),
        ("account-b", "meeting_audit", 1),
    }
    assert len(check_nodes(neo4j_session, "ZoomActivityEvent", ["id"]) or set()) == 5
    assert (
        len(
            check_rels(
                neo4j_session,
                "ZoomAccount",
                "id",
                "ZoomActivityEvent",
                "id",
                "RESOURCE",
            )
            or set()
        )
        == 5
    )

    assert (
        len(
            check_rels(
                neo4j_session,
                "ZoomActivityEvent",
                "id",
                "ZoomUser",
                "id",
                "PERFORMED_BY",
            )
            or set()
        )
        == 5
    )


@pytest.mark.parametrize("replacement_email", ["alice@example.com", "bob@example.com"])  # type: ignore[misc]
def test_report_identity_links_follow_current_email_mapping(
    neo4j_session: neo4j.Session,
    replacement_email: str,
) -> None:
    # Arrange
    users_a = seed(neo4j_session, "account-a")
    users_b = seed(neo4j_session, "account-b")
    client = MagicMock(spec=ZoomClient)
    deny_operations = False

    def pages(
        path: str,
        key: str,
        params: dict[str, Any] | None = None,
        page_size: int = 300,
    ) -> list[dict[str, Any]]:
        if path == "/report/activities":
            return [SIGNIN]
        if path == "/report/operationlogs":
            if deny_operations:
                response = requests.Response()
                response.status_code = 403
                raise requests.HTTPError(response=response)
            return [
                {
                    "operator": SIGNIN["email"],
                    "time": SIGNIN["time"],
                    "action": "Update",
                }
            ]
        if path == "/report/meeting_activities":
            return []
        raise AssertionError(path)

    client.get_paginated.side_effect = pages
    activity.sync_reports(neo4j_session, client, "account-a", 1, users_a, 1)
    activity.sync_reports(neo4j_session, client, "account-b", 1, users_b, 1)
    original_nodes = check_nodes(neo4j_session, "ZoomActivityEvent", ["id"])
    expected_links = (
        check_rels(
            neo4j_session, "ZoomActivityEvent", "id", "ZoomUser", "id", "PERFORMED_BY"
        )
        or set()
    )
    signin_id = next(
        node_id
        for node_id, account_id, source in (
            check_nodes(
                neo4j_session, "ZoomActivityEvent", ["id", "account_id", "source"]
            )
            or set()
        )
        if account_id == "account-a" and source == "signins"
    )
    expected_links.remove((signin_id, "account-a:user:user-1"))
    if replacement_email == SIGNIN["email"]:
        expected_links.add((signin_id, "account-a:user:user-2"))
    users_a[0]["email"] = "retired@example.com"
    users_a.append(
        {
            "id": "account-a:user:user-2",
            "zoom_id": "user-2",
            "email": replacement_email,
            "status": "active",
            "type": 2,
        }
    )
    load(
        neo4j_session, ZoomUserSchema(), users_a, ACCOUNT_ID="account-a", lastupdated=2
    )
    deny_operations = True

    # Act
    activity.sync_reports(neo4j_session, client, "account-a", 2, users_a, 1)

    # Assert
    assert check_nodes(neo4j_session, "ZoomActivityEvent", ["id"]) == original_nodes
    assert (
        check_rels(
            neo4j_session, "ZoomActivityEvent", "id", "ZoomUser", "id", "PERFORMED_BY"
        )
        == expected_links
    )
    assert check_nodes(
        neo4j_session, "ZoomActivityEvent", ["account_id", "source", "lastupdated"]
    ) == {
        ("account-a", "signins", 2),
        ("account-a", "operations", 1),
        ("account-b", "signins", 1),
        ("account-b", "operations", 1),
    }
    assert ("account-a:user:user-1", "retired@example.com") in (
        check_nodes(neo4j_session, "ZoomUser", ["id", "email"]) or set()
    )
