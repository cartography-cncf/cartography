from unittest.mock import MagicMock

import pytest

from cartography.intel.langsmith.user_groups import cleanup
from cartography.intel.langsmith.user_groups import get_user_groups
from cartography.intel.langsmith.user_groups import sync
from cartography.intel.langsmith.user_groups import transform_grants
from cartography.intel.langsmith.user_groups import transform_policy_attachments
from cartography.intel.langsmith.user_groups import transform_user_groups
from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.models.langsmith.usergroup import LangSmithUserGroupGrantSchema


def test_transform_user_groups_resolves_members_to_ls_user_ids():
    # Arrange
    groups = [{"id": "group-1", "name": "Support"}]
    members = {
        "group-1": [
            {"identity_id": "identity-homer"},
            {"identity_id": "identity-unknown"},
        ]
    }

    # Act
    (transformed,) = transform_user_groups(
        groups, members, {"identity-homer": "ls-homer"}
    )

    # Assert
    assert transformed["member_ls_user_ids"] == ["ls-homer"]


def test_transform_grants_scopes_role_ids_to_the_organization():
    # Act
    (grant,) = transform_grants(
        {"group-1": [{"workspace_id": "ws-1", "role_id": "role-1"}]}, "org-1"
    )

    # Assert
    assert grant["id"] == "group-1|ws-1"
    assert grant["role_id"] == "org-1|role-1"


def test_transform_policy_attachments_merges_scopes_of_the_same_policy():
    # Arrange
    policies = {
        "group-1": [
            {"id": "policy-1"},
            {"id": "policy-1", "workspace_id": "ws-2"},
            {"id": "policy-1", "workspace_id": "ws-1"},
            {"id": "policy-2", "workspace_id": "ws-1"},
        ]
    }

    # Act
    attachments = transform_policy_attachments(policies)

    # Assert
    assert attachments == [
        {
            "access_policy_id": "policy-1",
            "user_group_id": "group-1",
            "all_workspaces": True,
            "workspace_ids": ["ws-1", "ws-2"],
        },
        {
            "access_policy_id": "policy-2",
            "user_group_id": "group-1",
            "all_workspaces": False,
            "workspace_ids": ["ws-1"],
        },
    ]


@pytest.mark.parametrize(
    "status, expected_complete",
    # 403 also covers an organization without user groups, which can't be told apart
    # from a token that can't read them.
    [(404, True), (403, False), (None, False)],
)
def test_get_user_groups_reports_failures(status, expected_complete):
    # Arrange
    client = MagicMock()
    client.get_cursor_paginated.side_effect = LangSmithFetchError(
        "/user-groups", status, "failed"
    )

    # Act
    groups, complete = get_user_groups(client, "org-1")

    # Assert
    assert groups == []
    assert complete is expected_complete


def test_sync_skips_grants_of_workspace_scoped_user_groups(mocker):
    # Arrange
    client = MagicMock()
    client.get_cursor_paginated.side_effect = lambda path, **_: (
        [{"id": "org-group"}, {"id": "ws-group", "workspace_id": "ws-1"}]
        if path.endswith("/user-groups")
        else []
    )
    load = mocker.patch("cartography.intel.langsmith.user_groups.load_user_groups")
    cleanup = mocker.patch("cartography.intel.langsmith.user_groups.cleanup")

    # Act
    sync(MagicMock(), client, "org-1", {}, {"UPDATE_TAG": 1})

    # Assert
    # LangSmith answers 400 for a workspace-scoped user group's workspaces listing.
    requested = [call.args[0] for call in client.get_cursor_paginated.call_args_list]
    assert not any(path.endswith("/ws-group/workspaces") for path in requested)
    assert any(path.endswith("/org-group/workspaces") for path in requested)
    load.assert_called_once()
    assert cleanup.call_args.args[2:] == (True, True, True)


def test_failed_grant_cleanup_stops_before_group_cleanup(mocker):
    # Arrange
    session = MagicMock()
    parameters = {"ORG_ID": "org-1", "UPDATE_TAG": 2}
    cleanup_job = mocker.patch(
        "cartography.intel.langsmith.user_groups.cleanup_if_complete",
        side_effect=RuntimeError("cleanup failed"),
    )

    # Act
    with pytest.raises(RuntimeError, match="cleanup failed"):
        cleanup(
            session,
            parameters,
            members_complete=True,
            grants_complete=True,
            policies_complete=True,
        )

    # Assert
    cleanup_job.assert_called_once_with(
        session, LangSmithUserGroupGrantSchema(), True, parameters
    )
