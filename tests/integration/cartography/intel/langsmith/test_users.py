from unittest.mock import patch

import cartography.intel.langsmith.users
import tests.data.langsmith.users
from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.roles import CUSTOM_ROLE_ID
from tests.data.langsmith.roles import ORG_ADMIN_ROLE_ID
from tests.data.langsmith.roles import WORKSPACE_VIEWER_ROLE_ID
from tests.data.langsmith.users import BART_LS_USER_ID
from tests.data.langsmith.users import HOMER_LS_USER_ID
from tests.data.langsmith.users import MARGE_LS_USER_ID
from tests.data.langsmith.workspaces import WORKSPACE_DEV_ID
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID
from tests.integration.cartography.intel.langsmith.test_roles import (
    _ensure_local_neo4j_has_test_roles,
)
from tests.integration.cartography.intel.langsmith.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _mock_get_workspace_members(client, org_id, workspace_id):
    return tests.data.langsmith.users.LANGSMITH_WORKSPACE_MEMBERS[workspace_id]


def _ensure_local_neo4j_has_test_users(neo4j_session):
    users = cartography.intel.langsmith.users.transform_users(
        tests.data.langsmith.users.LANGSMITH_ACTIVE_ORG_MEMBERS,
        tests.data.langsmith.users.LANGSMITH_PENDING_ORG_MEMBERS,
    )
    memberships = []
    for workspace_id in (WORKSPACE_PROD_ID, WORKSPACE_DEV_ID):
        memberships.extend(
            cartography.intel.langsmith.users.transform_memberships(
                workspace_id,
                tests.data.langsmith.users.LANGSMITH_WORKSPACE_MEMBERS[workspace_id],
            )
        )
    cartography.intel.langsmith.users.load_users(
        neo4j_session, users, memberships, LANGSMITH_ORG_ID, TEST_UPDATE_TAG
    )
    return users


@patch.object(
    cartography.intel.langsmith.users,
    "get_workspace_members",
    side_effect=_mock_get_workspace_members,
)
@patch.object(
    cartography.intel.langsmith.users,
    "get_pending_members",
    return_value=tests.data.langsmith.users.LANGSMITH_PENDING_ORG_MEMBERS,
)
@patch.object(
    cartography.intel.langsmith.users,
    "get_active_members",
    return_value=tests.data.langsmith.users.LANGSMITH_ACTIVE_ORG_MEMBERS,
)
def test_sync_langsmith_users(mock_active, mock_pending, mock_ws, neo4j_session):
    _ensure_local_neo4j_has_test_roles(neo4j_session)
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": LANGSMITH_ORG_ID,
    }

    cartography.intel.langsmith.users.sync(
        neo4j_session,
        None,
        LANGSMITH_ORG_ID,
        [WORKSPACE_PROD_ID, WORKSPACE_DEV_ID],
        common_job_parameters,
    )

    # Users are keyed on ls_user_id, not on the identity (membership) UUID. The pending
    # invite has no ls_user_id yet and must not appear.
    assert check_nodes(
        neo4j_session, "LangSmithUser", ["id", "email", "is_disabled"]
    ) == {
        (MARGE_LS_USER_ID, "mbsimpson@simpson.corp", False),
        (HOMER_LS_USER_ID, "hjsimpson@simpson.corp", False),
        (BART_LS_USER_ID, "bjsimpson@simpson.corp", True),
    }

    assert check_rels(
        neo4j_session,
        "LangSmithUser",
        "id",
        "LangSmithRole",
        "id",
        "HAS_ROLE",
        rel_direction_right=True,
    ) == {(MARGE_LS_USER_ID, ORG_ADMIN_ROLE_ID)}

    assert check_rels(
        neo4j_session,
        "LangSmithUser",
        "id",
        "LangSmithWorkspace",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (MARGE_LS_USER_ID, WORKSPACE_PROD_ID),
        (MARGE_LS_USER_ID, WORKSPACE_DEV_ID),
        (HOMER_LS_USER_ID, WORKSPACE_PROD_ID),
        (BART_LS_USER_ID, WORKSPACE_DEV_ID),
    }


@patch.object(
    cartography.intel.langsmith.users,
    "get_workspace_members",
    side_effect=_mock_get_workspace_members,
)
@patch.object(
    cartography.intel.langsmith.users,
    "get_pending_members",
    return_value=tests.data.langsmith.users.LANGSMITH_PENDING_ORG_MEMBERS,
)
@patch.object(
    cartography.intel.langsmith.users,
    "get_active_members",
    return_value=tests.data.langsmith.users.LANGSMITH_ACTIVE_ORG_MEMBERS,
)
def test_workspace_membership_carries_role(
    mock_active, mock_pending, mock_ws, neo4j_session
):
    """
    The (user, workspace, role) triple must stay intact: the same user can hold different
    roles in different workspaces, which a plain user->role edge could not express.
    """
    _ensure_local_neo4j_has_test_roles(neo4j_session)
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)

    cartography.intel.langsmith.users.sync(
        neo4j_session,
        None,
        LANGSMITH_ORG_ID,
        [WORKSPACE_PROD_ID, WORKSPACE_DEV_ID],
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": LANGSMITH_ORG_ID},
    )

    assert check_rels(
        neo4j_session,
        "LangSmithUser",
        "id",
        "LangSmithWorkspaceMembership",
        "id",
        "HAS_MEMBERSHIP",
        rel_direction_right=True,
    ) == {
        (MARGE_LS_USER_ID, f"{MARGE_LS_USER_ID}|{WORKSPACE_PROD_ID}"),
        (HOMER_LS_USER_ID, f"{HOMER_LS_USER_ID}|{WORKSPACE_PROD_ID}"),
        (BART_LS_USER_ID, f"{BART_LS_USER_ID}|{WORKSPACE_DEV_ID}"),
    }

    assert check_rels(
        neo4j_session,
        "LangSmithWorkspaceMembership",
        "id",
        "LangSmithRole",
        "id",
        "HAS_ROLE",
        rel_direction_right=True,
    ) == {
        (f"{MARGE_LS_USER_ID}|{WORKSPACE_PROD_ID}", CUSTOM_ROLE_ID),
        (f"{HOMER_LS_USER_ID}|{WORKSPACE_PROD_ID}", WORKSPACE_VIEWER_ROLE_ID),
        (f"{BART_LS_USER_ID}|{WORKSPACE_DEV_ID}", CUSTOM_ROLE_ID),
    }

    assert check_rels(
        neo4j_session,
        "LangSmithWorkspaceMembership",
        "id",
        "LangSmithWorkspace",
        "id",
        "IN_WORKSPACE",
        rel_direction_right=True,
    ) == {
        (f"{MARGE_LS_USER_ID}|{WORKSPACE_PROD_ID}", WORKSPACE_PROD_ID),
        (f"{HOMER_LS_USER_ID}|{WORKSPACE_PROD_ID}", WORKSPACE_PROD_ID),
        (f"{BART_LS_USER_ID}|{WORKSPACE_DEV_ID}", WORKSPACE_DEV_ID),
    }
