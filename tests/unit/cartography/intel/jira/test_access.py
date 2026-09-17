from copy import deepcopy
from unittest.mock import Mock

import pytest
import requests

from cartography.config import Config
from cartography.intel.jira import start_jira_ingestion
from cartography.intel.jira.access import get
from cartography.intel.jira.access import resource_id
from cartography.intel.jira.access import transform
from cartography.intel.jira.util import JiraClient
from tests.data.jira.access import CLOUD_ID


def response(payload, status=200):
    result = requests.Response()
    result.status_code = status
    result.json = Mock(return_value=payload)
    return result


def test_pagination_uses_server_page_size_and_continues_short_user_pages():
    # Arrange
    client = JiraClient(CLOUD_ID, "reader@example.com", "test-token")
    client.session.get = Mock(
        side_effect=[
            response([{"accountId": "1"}]),
            response([{"accountId": "2"}]),
            response([]),
            response(
                {
                    "values": [{"groupId": "1"}],
                    "startAt": 0,
                    "total": 2,
                    "isLast": False,
                }
            ),
            response(
                {"values": [{"groupId": "2"}], "startAt": 1, "total": 2, "isLast": True}
            ),
        ]
    )
    # Act
    users = client.pages("users/search")
    groups = client.pages("group/bulk")
    # Assert
    assert users == [{"accountId": "1"}, {"accountId": "2"}]
    assert groups == [{"groupId": "1"}, {"groupId": "2"}]
    assert [
        call.kwargs["params"]["startAt"] for call in client.session.get.call_args_list
    ] == [0, 1, 2, 0, 1]
    assert all(
        call.kwargs["allow_redirects"] is False
        for call in client.session.get.call_args_list
    )


@pytest.mark.parametrize(
    "payloads",
    [
        [{"values": [], "startAt": 0, "isLast": False}],
        [{"values": [{"groupId": "1"}], "startAt": 1, "isLast": True}],
        [{"values": []}],
        [{"values": [], "startAt": 0, "isLast": "false"}],
        [{"values": [], "startAt": 0, "isLast": True, "total": 2}],
    ],
)
def test_incomplete_page_raises(payloads):
    # Arrange
    client = JiraClient(CLOUD_ID, "reader@example.com", "test-token")
    client.session.get = Mock(side_effect=[response(p) for p in payloads])
    # Act and assert
    with pytest.raises((ValueError, KeyError)):
        client.pages("group/bulk")


def test_repeated_user_page_raises():
    # Arrange
    client = JiraClient(CLOUD_ID, "reader@example.com", "test-token")
    client.session.get = Mock(return_value=response([{"accountId": "1"}]))
    # Act and assert
    with pytest.raises(ValueError, match="repeated"):
        client.pages("users/search")


@pytest.mark.parametrize("status", [302, 401, 403, 429, 500])
def test_http_errors_and_redirects_raise(status):
    # Arrange
    client = JiraClient(CLOUD_ID, "reader@example.com", "test-token")
    result = response({}, status)
    result.headers["Location"] = "https://untrusted.example"
    client.session.get = Mock(return_value=result)
    # Act and assert
    with pytest.raises(requests.HTTPError):
        client.get("serverInfo")


@pytest.mark.parametrize(
    "url",
    [
        "http://example.atlassian.net",
        "https://example.atlassian.net.evil.example",
        "https://reader:secret@example.atlassian.net",
        "https://example.atlassian.net/path",
    ],
)
def test_reject_unsafe_credential_destinations(url):
    # Act and assert
    with pytest.raises(ValueError, match="HTTPS"):
        JiraClient(CLOUD_ID, "reader@example.com", "test-token", url)


def test_missing_permission_aborts_before_inventory():
    # Arrange
    client = Mock()
    client.get.return_value = {
        "permissions": {
            "ADMINISTER": {"havePermission": False},
            "BROWSE_USERS": {"havePermission": True},
        }
    }
    # Act and assert
    with pytest.raises(PermissionError):
        get(client)
    client.pages.assert_not_called()


def test_unconfigured_skips():
    # Arrange
    session = Mock()
    # Act
    start_jira_ingestion(session, Config(neo4j_uri="bolt://unused"))
    # Assert
    session.run.assert_not_called()


def test_ids_are_tenant_scoped_and_unambiguous():
    # Act and assert
    assert resource_id("site-a", "role", "1:2", "3") != resource_id(
        "site-a", "role", "1", "2:3"
    )
    assert resource_id("site-a", "user", "same") != resource_id(
        "site-b", "user", "same"
    )
    with pytest.raises(ValueError):
        resource_id(CLOUD_ID, "user", "unknown")


def test_shared_permission_scheme_fetched_once():
    # Arrange
    client = Mock()
    client.get.side_effect = lambda path, **params: {
        "mypermissions": {
            "permissions": {
                p: {"havePermission": True} for p in ("ADMINISTER", "BROWSE_USERS")
            }
        },
        "serverInfo": {"deploymentType": "Cloud"},
        "project/1/roledetails": [],
        "project/2/roledetails": [],
        "project/1/permissionscheme": {"id": 42},
        "project/2/permissionscheme": {"id": 42},
        "permissionscheme/42": {"id": 42, "permissions": []},
    }[path]
    client.pages.side_effect = lambda path, **params: (
        [{"id": "1"}, {"id": "2"}] if path == "project/search" else []
    )
    # Act
    raw = get(client)
    # Assert
    assert len(raw["schemes"]) == 1
    assert (
        sum(c.args[0] == "permissionscheme/42" for c in client.get.call_args_list) == 1
    )


def test_renamed_group_resolves_by_stable_id_and_empty_group_stays_conditional():
    # Arrange
    from tests.data.jira.access import API_RESPONSES
    from tests.data.jira.access import GROUPS
    from tests.data.jira.access import PROJECTS
    from tests.data.jira.access import ROLE
    from tests.data.jira.access import SCHEME
    from tests.data.jira.access import USERS

    scheme = deepcopy(SCHEME)
    scheme["permissions"].append(
        {"id": 5, "permission": "BROWSE_PROJECTS", "holder": {"type": "group"}}
    )
    raw = {
        "info": API_RESPONSES["serverInfo"],
        "groups": deepcopy(GROUPS),
        "users": USERS,
        "admin_groups": {"admin": [GROUPS[1]], "site-admin": []},
        "memberships": {},
        "projects": [{**PROJECTS[0], "permission_scheme_id": "500"}],
        "roles": {"100": [ROLE]},
        "schemes": {"500": scheme},
    }
    raw["groups"][1]["name"] = "Renamed admins"
    # Act
    data = transform(raw, CLOUD_ID)
    # Assert
    assert data["grants"][1]["group_id"] == resource_id(CLOUD_ID, "group", "group-2")
    assert data["grants"][-1]["group_id"] is None
    assert data["users"][1]["email"] is None
