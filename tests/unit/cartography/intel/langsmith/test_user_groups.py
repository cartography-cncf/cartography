from unittest.mock import MagicMock

import pytest

from cartography.intel.langsmith.user_groups import get_user_groups
from cartography.intel.langsmith.user_groups import transform_grants
from cartography.intel.langsmith.user_groups import transform_policy_attachments
from cartography.intel.langsmith.user_groups import transform_user_groups
from cartography.intel.langsmith.util import LangSmithFetchError


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
