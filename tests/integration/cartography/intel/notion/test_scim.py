from copy import deepcopy
from unittest.mock import MagicMock

import pytest

import cartography.intel.notion.scim
import cartography.intel.notion.users
import cartography.intel.notion.workspaces
from cartography.intel.notion.scim import ENTERPRISE_USER_EXTENSION
from cartography.intel.notion.scim import NOTION_USER_EXTENSION
from tests.data.notion.scim import SCIM_GROUPS
from tests.data.notion.scim import SCIM_USERS
from tests.data.notion.users import USERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 223456789


def _response(payload):
    response = MagicMock()
    response.json.return_value = payload
    return response


def _public_session(raw_users=USERS):
    session = MagicMock()
    session.get.return_value = _response(
        {"results": raw_users, "has_more": False, "next_cursor": None},
    )
    return session


def _scim_response(resources):
    return _response(
        {
            "Resources": resources,
            "totalResults": len(resources),
            "startIndex": 1,
            "itemsPerPage": len(resources),
        },
    )


def _scim_session(scim_users=SCIM_USERS, scim_groups=SCIM_GROUPS):
    session = MagicMock()
    session.get.side_effect = [
        _scim_response(scim_users),
        _scim_response(scim_groups),
    ]
    return session


def _sync_core(neo4j_session, workspace_id, update_tag):
    cartography.intel.notion.workspaces.sync(
        neo4j_session,
        workspace_id,
        workspace_id,
        update_tag,
    )
    return cartography.intel.notion.users.sync(
        neo4j_session,
        _public_session(),
        workspace_id,
        update_tag,
        {"UPDATE_TAG": update_tag, "WORKSPACE_ID": workspace_id},
    )


def _sync_scim(
    neo4j_session,
    workspace_id,
    update_tag,
    scim_users=SCIM_USERS,
    scim_groups=SCIM_GROUPS,
):
    public_people = _sync_core(neo4j_session, workspace_id, update_tag)
    cartography.intel.notion.scim.sync(
        neo4j_session,
        _scim_session(scim_users, scim_groups),
        public_people,
        workspace_id,
        update_tag,
        {"UPDATE_TAG": update_tag, "WORKSPACE_ID": workspace_id},
    )


def test_sync_scim_users_groups_memberships_and_reporting(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act
    _sync_scim(neo4j_session, "workspace-1", TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "NotionUser",
        ["id", "active", "workspace_role", "department", "is_workspace_member"],
    ) == {
        ("workspace-1/person-1", True, "owner", "Security", True),
        ("workspace-1/person-2", True, "member", None, True),
    }
    assert check_nodes(
        neo4j_session,
        "NotionGroup",
        ["id", "name", "scim_external_id"],
    ) == {("workspace-1/group-1", "Security", "security-team")}
    assert check_rels(
        neo4j_session,
        "NotionUser",
        "id",
        "NotionGroup",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        ("workspace-1/person-1", "workspace-1/group-1"),
        ("workspace-1/person-2", "workspace-1/group-1"),
    }
    assert check_rels(
        neo4j_session,
        "NotionUser",
        "id",
        "NotionUser",
        "id",
        "REPORTS_TO",
        rel_direction_right=True,
    ) == {("workspace-1/person-2", "workspace-1/person-1")}
    ontology = neo4j_session.run(
        """
        MATCH (u:NotionUser {id: 'workspace-1/person-1'})
        MATCH (g:NotionGroup {id: 'workspace-1/group-1'})
        RETURN u._ont_active AS active, g._ont_name AS group_name
        """,
    ).single()
    assert ontology == {"active": True, "group_name": "Security"}


def test_scim_refresh_cleans_stale_groups_memberships_and_manager(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_scim(neo4j_session, "workspace-1", TEST_UPDATE_TAG)
    updated_users = deepcopy(SCIM_USERS)
    updated_users[1]["active"] = False
    updated_users[1][NOTION_USER_EXTENSION]["role"] = "restricted_member"
    updated_users[1][ENTERPRISE_USER_EXTENSION].pop("manager")

    # Act
    _sync_scim(
        neo4j_session,
        "workspace-1",
        TEST_UPDATE_TAG + 1,
        updated_users,
        [],
    )

    # Assert
    assert check_nodes(neo4j_session, "NotionGroup", ["id"]) == set()
    assert (
        check_rels(
            neo4j_session,
            "NotionUser",
            "id",
            "NotionGroup",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "NotionUser",
            "id",
            "NotionUser",
            "id",
            "REPORTS_TO",
            rel_direction_right=True,
        )
        == set()
    )
    bob = neo4j_session.run(
        """
        MATCH (u:NotionUser {id: 'workspace-1/person-2'})
        RETURN u.active AS active, u.workspace_role AS role,
               u.manager_email AS manager_email
        """,
    ).single()
    assert bob == {
        "active": False,
        "role": "restricted_member",
        "manager_email": None,
    }


def test_no_scim_run_preserves_existing_scim_data(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_scim(neo4j_session, "workspace-1", TEST_UPDATE_TAG)

    # Act: this is the exact path used when scim_token is omitted.
    _sync_core(neo4j_session, "workspace-1", TEST_UPDATE_TAG + 1)

    # Assert
    assert check_nodes(
        neo4j_session,
        "NotionUser",
        ["id", "workspace_role", "is_workspace_member", "active", "_ont_active"],
    ) == {
        ("workspace-1/person-1", "owner", True, True, True),
        ("workspace-1/person-2", "member", True, True, True),
    }
    assert check_nodes(neo4j_session, "NotionGroup", ["id"]) == {
        ("workspace-1/group-1",),
    }


def test_failed_scim_enumeration_suppresses_all_scim_updates_and_cleanup(
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_scim(neo4j_session, "workspace-1", TEST_UPDATE_TAG)
    public_people = _sync_core(neo4j_session, "workspace-1", TEST_UPDATE_TAG + 1)
    failed_session = MagicMock()
    failed_session.get.side_effect = [
        _scim_response([]),
        _response(
            {
                "Resources": "malformed",
                "totalResults": 0,
                "startIndex": 1,
                "itemsPerPage": 0,
            },
        ),
    ]

    # Act and assert
    with pytest.raises(ValueError):
        cartography.intel.notion.scim.sync(
            neo4j_session,
            failed_session,
            public_people,
            "workspace-1",
            TEST_UPDATE_TAG + 1,
            {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "WORKSPACE_ID": "workspace-1"},
        )
    assert check_nodes(
        neo4j_session,
        "NotionUser",
        ["id", "workspace_role"],
    ) == {
        ("workspace-1/person-1", "owner"),
        ("workspace-1/person-2", "member"),
    }
    assert check_nodes(neo4j_session, "NotionGroup", ["id"]) == {
        ("workspace-1/group-1",),
    }


def test_scim_cleanup_is_scoped_to_workspace(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_scim(neo4j_session, "workspace-1", TEST_UPDATE_TAG)
    _sync_scim(neo4j_session, "workspace-2", TEST_UPDATE_TAG)

    # Act
    _sync_scim(neo4j_session, "workspace-1", TEST_UPDATE_TAG + 1, SCIM_USERS, [])

    # Assert
    assert check_nodes(neo4j_session, "NotionGroup", ["id"]) == {
        ("workspace-2/group-1",),
    }
    assert check_rels(
        neo4j_session,
        "NotionUser",
        "id",
        "NotionGroup",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        ("workspace-2/person-1", "workspace-2/group-1"),
        ("workspace-2/person-2", "workspace-2/group-1"),
    }
