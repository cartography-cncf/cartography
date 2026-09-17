from copy import deepcopy
from unittest.mock import Mock

import pytest
import requests

from cartography.intel.jira.access import resource_id
from cartography.intel.jira.access import sync
from cartography.intel.jira.util import JiraClient
from cartography.intel.ontology.users import sync as sync_ontology_users
from tests.data.jira.access import API_RESPONSES
from tests.data.jira.access import CLOUD_ID
from tests.data.jira.access import GROUPS
from tests.data.jira.access import OTHER_CLOUD_ID
from tests.data.jira.access import PROJECTS
from tests.data.jira.access import USERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def api_client(cloud_id=CLOUD_ID):
    """Mock only the provider client boundary; exercise real orchestration and graph writes."""
    client = Mock(spec=JiraClient)
    client.cloud_id = cloud_id
    state = {
        "responses": deepcopy(API_RESPONSES),
        "users": deepcopy(USERS),
        "groups": deepcopy(GROUPS),
        "projects": deepcopy(PROJECTS),
        "memberships": {"group-1": deepcopy(USERS), "group-2": [deepcopy(USERS[0])]},
        "admin": [deepcopy(GROUPS[1])],
        "site-admin": [deepcopy(GROUPS[1])],
    }

    def pages(path, **params):
        if path == "users/search":
            return deepcopy(state["users"])
        if path == "group/bulk":
            return deepcopy(state[params.get("accessType", "groups")])
        if path == "group/member":
            assert params["includeInactiveUsers"] == "true"
            return deepcopy(state["memberships"][params["groupId"]])
        if path == "project/search":
            return deepcopy(state["projects"])
        raise AssertionError(path)

    client.pages.side_effect = pages
    client.get.side_effect = lambda path, **params: deepcopy(state["responses"][path])
    return client, state


def test_sync_access_graph_and_ontology(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    client, _ = api_client()
    # Act
    sync(neo4j_session, client, 1)
    sync_ontology_users(neo4j_session, ["jira"], 1, {"UPDATE_TAG": 1})
    # Assert
    assert check_nodes(neo4j_session, "JiraUser", ["account_id", "active"]) == {
        ("user-1", True),
        ("user-2", False),
    }
    assert check_rels(
        neo4j_session,
        "JiraUser",
        "account_id",
        "JiraGroup",
        "group_id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {("user-1", "group-1"), ("user-1", "group-2"), ("user-2", "group-1")}
    assert check_rels(
        neo4j_session,
        "JiraGroup",
        "group_id",
        "JiraTenant",
        "id",
        "ADMIN_OF",
        rel_direction_right=True,
    ) == {("group-2", CLOUD_ID)}
    assert check_rels(
        neo4j_session,
        "JiraProjectRole",
        "id",
        "JiraProject",
        "project_id",
        "ROLE_OF",
        rel_direction_right=True,
    ) == {
        (resource_id(CLOUD_ID, "role", "100", 10), "100"),
        (resource_id(CLOUD_ID, "role", "200", 10), "200"),
    }
    assert check_rels(
        neo4j_session,
        "JiraProjectRole",
        "id",
        "JiraPermissionGrant",
        "grant_id",
        "HAS_PERMISSION",
        rel_direction_right=True,
    ) == {(resource_id(CLOUD_ID, "role", "100", 10), "1")}
    assert check_rels(
        neo4j_session,
        "JiraUser",
        "account_id",
        "JiraPermissionGrant",
        "grant_id",
        "HAS_PERMISSION",
        rel_direction_right=True,
    ) == {("user-1", "3")}
    assert check_rels(
        neo4j_session,
        "User",
        "email",
        "JiraUser",
        "account_id",
        "HAS_ACCOUNT",
        rel_direction_right=True,
    ) == {("user@example.com", "user-1")}
    row = neo4j_session.run(
        "MATCH (u:JiraUser {account_id: 'user-1'}) RETURN u._ont_source AS source, u._ont_email AS email, u._ont_active AS active"
    ).single()
    assert dict(row) == {"source": "jira", "email": "user@example.com", "active": True}
    assert check_nodes(
        neo4j_session, "JiraProject", ["project_id", "permission_scheme_supported"]
    ) == {("100", True), ("200", False)}
    row = neo4j_session.run(
        "MATCH (g:JiraPermissionGrant {holder_type: 'anyone'}) RETURN g.permission AS permission, COUNT { (g)<-[:HAS_PERMISSION]-() } AS holders"
    ).single()
    assert dict(row) == {"permission": "BROWSE_PROJECTS", "holders": 0}


def test_cleanup_removes_stale_nodes_and_edges_without_cross_tenant_loss(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    client, state = api_client()
    other, _ = api_client(OTHER_CLOUD_ID)
    sync(neo4j_session, client, 1)
    sync(neo4j_session, other, 1)
    state["users"] = [deepcopy(USERS[0])]
    state["memberships"] = {"group-1": [], "group-2": [deepcopy(USERS[0])]}
    state["projects"] = [deepcopy(PROJECTS[0])]
    state["responses"]["project/100/role/10"]["actors"] = []
    state["responses"]["permissionscheme/500"]["permissions"] = []
    state["admin"] = state["site-admin"] = []
    # Act
    sync(neo4j_session, client, 2)
    # Assert
    assert check_nodes(neo4j_session, "JiraUser", ["tenant_id", "account_id"]) == {
        (CLOUD_ID, "user-1"),
        (OTHER_CLOUD_ID, "user-1"),
        (OTHER_CLOUD_ID, "user-2"),
    }
    assert check_nodes(neo4j_session, "JiraProject", ["tenant_id", "project_id"]) == {
        (CLOUD_ID, "100"),
        (OTHER_CLOUD_ID, "100"),
        (OTHER_CLOUD_ID, "200"),
    }
    assert check_rels(
        neo4j_session,
        "JiraGroup",
        "tenant_id",
        "JiraTenant",
        "id",
        "ADMIN_OF",
        rel_direction_right=True,
    ) == {(OTHER_CLOUD_ID, OTHER_CLOUD_ID)}
    assert (
        neo4j_session.run(
            "MATCH (r:JiraProjectRole {tenant_id: $id})<-[:MEMBER_OF]-() RETURN count(r) AS count",
            id=CLOUD_ID,
        ).single()["count"]
        == 0
    )
    assert check_nodes(
        neo4j_session, "JiraPermissionGrant", ["tenant_id", "grant_id"]
    ) == {(OTHER_CLOUD_ID, str(i)) for i in range(1, 5)}
    assert check_rels(
        neo4j_session,
        "JiraUser",
        "id",
        "JiraGroup",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (
            resource_id(CLOUD_ID, "user", "user-1"),
            resource_id(CLOUD_ID, "group", "group-2"),
        ),
        *(
            (
                resource_id(OTHER_CLOUD_ID, "user", u),
                resource_id(OTHER_CLOUD_ID, "group", g),
            )
            for u, g in [
                ("user-1", "group-1"),
                ("user-1", "group-2"),
                ("user-2", "group-1"),
            ]
        ),
    }


def test_late_api_failure_preserves_entire_previous_snapshot(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    client, state = api_client()
    sync(neo4j_session, client, 1)
    before = neo4j_session.run("MATCH (n) RETURN count(n) AS count").single()["count"]

    def get_with_failure(path, **params):
        if path == "project/200/role/10":
            raise requests.HTTPError("403 Forbidden")
        return deepcopy(state["responses"][path])

    client.get.side_effect = get_with_failure
    # Act and assert
    with pytest.raises(requests.HTTPError):
        sync(neo4j_session, client, 2)
    assert (
        neo4j_session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
        == before
    )
    assert (
        neo4j_session.run(
            "MATCH (n) WHERE n.lastupdated <> 1 RETURN count(n) AS count"
        ).single()["count"]
        == 0
    )


def test_deleted_user_tombstones_leave_references_unlinked(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    client, state = api_client()
    sync(neo4j_session, client, 1)
    tombstone = {"accountId": "unknown", "active": False, "displayName": "Former user"}
    state["users"].append(tombstone)
    state["memberships"]["group-1"].append(tombstone)
    state["projects"][0]["lead"] = tombstone
    state["responses"]["project/100/role/10"]["actors"].append(
        {"type": "atlassian-user-role-actor", "actorUser": {"accountId": "unknown"}}
    )
    state["responses"]["permissionscheme/500"]["permissions"][2]["holder"][
        "parameter"
    ] = "unknown"
    state["responses"]["permissionscheme/500"]["permissions"].extend(
        [
            {
                "id": 5,
                "permission": "BROWSE_PROJECTS",
                "holder": {"type": "user", "parameter": "user-1"},
            },
            {
                "id": 6,
                "permission": "ADMINISTER_PROJECTS",
                "holder": {"type": "projectLead"},
            },
        ]
    )
    # Act
    sync(neo4j_session, client, 2)
    # Assert
    assert check_nodes(neo4j_session, "JiraUser", ["account_id", "lastupdated"]) == {
        ("user-1", 2),
        ("user-2", 2),
    }
    assert check_nodes(neo4j_session, "JiraProject", ["project_id", "lastupdated"]) == {
        ("100", 2),
        ("200", 2),
    }
    assert check_rels(
        neo4j_session,
        "JiraUser",
        "account_id",
        "JiraGroup",
        "group_id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {("user-1", "group-1"), ("user-1", "group-2"), ("user-2", "group-1")}
    assert check_rels(
        neo4j_session,
        "JiraUser",
        "account_id",
        "JiraProjectRole",
        "role_id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {("user-1", "10")}
    assert (
        check_rels(
            neo4j_session,
            "JiraUser",
            "account_id",
            "JiraProject",
            "project_id",
            "LEADS",
            rel_direction_right=True,
        )
        == set()
    )
    assert check_nodes(neo4j_session, "JiraPermissionGrant", ["grant_id"]) == {
        (str(i),) for i in range(1, 7)
    }
    assert check_rels(
        neo4j_session,
        "JiraUser",
        "account_id",
        "JiraPermissionGrant",
        "grant_id",
        "HAS_PERMISSION",
        rel_direction_right=True,
    ) == {("user-1", "5")}
