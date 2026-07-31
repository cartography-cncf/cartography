import asyncio
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.modal.environment_roles
import cartography.intel.modal.members
import cartography.intel.modal.proxy_tokens
import cartography.intel.modal.service_users
import tests.data.modal.identity
from tests.integration.cartography.intel.modal.test_environments import (
    _ensure_local_neo4j_has_test_environments,
)
from tests.integration.cartography.intel.modal.test_workspace import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.cartography.intel.modal.test_workspace import TEST_UPDATE_TAG
from tests.integration.cartography.intel.modal.test_workspace import TEST_WORKSPACE_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ENVIRONMENT_ID = "en-C3umado26sLFrhYfZjoWjL"


def _workspace_params():
    return {"UPDATE_TAG": TEST_UPDATE_TAG, "WORKSPACE_ID": TEST_WORKSPACE_ID}


def _ensure_local_neo4j_has_test_members(
    neo4j_session, workspace_id=TEST_WORKSPACE_ID, raw=None
):
    """Seed the users, their memberships and the builtin roles. Returns the username map."""
    raw = tests.data.modal.identity.MODAL_WORKSPACE_MEMBERS if raw is None else raw
    cartography.intel.modal.members.load_roles(
        neo4j_session,
        cartography.intel.modal.members.transform_roles(workspace_id),
        workspace_id,
        TEST_UPDATE_TAG,
    )
    users = cartography.intel.modal.members.transform(raw)
    cartography.intel.modal.members.load_users(neo4j_session, users, TEST_UPDATE_TAG)
    cartography.intel.modal.members.load_memberships(
        neo4j_session,
        cartography.intel.modal.members.transform_memberships(raw, workspace_id),
        workspace_id,
        TEST_UPDATE_TAG,
    )
    return cartography.intel.modal.members.user_ids_by_username(users)


def _ensure_local_neo4j_has_test_service_users(
    neo4j_session, user_ids_by_username=None
):
    cartography.intel.modal.service_users.load_service_users(
        neo4j_session,
        cartography.intel.modal.service_users.transform(
            tests.data.modal.identity.MODAL_SERVICE_USERS,
            user_ids_by_username or {},
        ),
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.modal.members,
    "list_workspace_members",
    return_value=tests.data.modal.identity.MODAL_WORKSPACE_MEMBERS,
)
def test_load_modal_users_and_memberships(mock_list, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    # Act
    asyncio.run(
        cartography.intel.modal.members.sync(
            neo4j_session, MagicMock(), _workspace_params()
        )
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "ModalUser",
        ["id", "email", "identity_provider_type"],
    ) == {
        (
            "us-ydIZVCWluEtzFTbpJvjHcK",
            "alice@example.com",
            "IDENTITY_PROVIDER_TYPE_GOOGLE_OAUTH",
        ),
        (
            "us-2QpLmNrTvBxWsZdKfGhYjA",
            "bob@example.com",
            "IDENTITY_PROVIDER_TYPE_GITHUB",
        ),
    }
    assert check_nodes(neo4j_session, "ModalWorkspaceRole", ["name", "scope"]) == {
        ("member", "workspace"),
        ("manager", "workspace"),
        ("owner", "workspace"),
    }
    # MEMBER_ROLE_USER normalises to "member", MEMBER_ROLE_OWNER to "owner".
    assert check_rels(
        neo4j_session,
        "ModalUser",
        "email",
        "ModalWorkspaceRole",
        "name",
        "HAS_ROLE",
    ) == {
        ("alice@example.com", "owner"),
        ("bob@example.com", "member"),
    }


@patch.object(
    cartography.intel.modal.service_users,
    "list_service_users",
    return_value=tests.data.modal.identity.MODAL_SERVICE_USERS,
)
def test_load_modal_service_users_and_tokens(mock_list, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    usernames = _ensure_local_neo4j_has_test_members(neo4j_session)

    # Act
    asyncio.run(
        cartography.intel.modal.service_users.sync(
            neo4j_session, MagicMock(), _workspace_params(), usernames
        )
    )

    # Assert
    assert check_nodes(neo4j_session, "ModalServiceUser", ["id", "name"]) == {
        ("su-8HjKlZxCvBnMqWeRtYuIoP", "ci-bot"),
        ("su-1AsDfGhJkLzXcVbNmQwErT", "stale-bot"),
    }
    assert check_nodes(neo4j_session, "ModalApiToken", ["id", "name"]) == {
        ("ak-4pE5t96YiNM0svmOjIet7z", "ci-bot"),
        ("ak-9ZxCvBnMqWeRtYuIoPaSdF", "stale-bot"),
    }
    # OWNED_BY is the canonical APIKey -> ServiceAccount edge.
    assert check_rels(
        neo4j_session,
        "ModalApiToken",
        "id",
        "ModalServiceUser",
        "id",
        "OWNED_BY",
    ) == {
        ("ak-4pE5t96YiNM0svmOjIet7z", "su-8HjKlZxCvBnMqWeRtYuIoP"),
        ("ak-9ZxCvBnMqWeRtYuIoPaSdF", "su-1AsDfGhJkLzXcVbNmQwErT"),
    }


@patch.object(
    cartography.intel.modal.service_users,
    "list_service_users",
    return_value=tests.data.modal.identity.MODAL_SERVICE_USERS,
)
def test_modal_service_user_created_by_resolves_username_to_user_id(
    mock_list, neo4j_session
):
    """Modal reports the creator as a workspace username, which the intel layer resolves to a
    ModalUser id against this workspace's members. 'stale-bot' was created by a username with
    no matching member, so it must get no edge rather than a wrong one."""
    # Arrange
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    usernames = _ensure_local_neo4j_has_test_members(neo4j_session)

    # Act
    asyncio.run(
        cartography.intel.modal.service_users.sync(
            neo4j_session, MagicMock(), _workspace_params(), usernames
        )
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "ModalServiceUser",
        "name",
        "ModalUser",
        "display_name",
        "CREATED_BY",
    ) == {("ci-bot", "alice")}


@patch.object(
    cartography.intel.modal.proxy_tokens,
    "list_proxy_tokens",
    return_value=tests.data.modal.identity.MODAL_PROXY_TOKENS,
)
def test_load_modal_proxy_tokens(mock_list, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    # Act
    asyncio.run(
        cartography.intel.modal.proxy_tokens.sync(
            neo4j_session, MagicMock(), _workspace_params()
        )
    )

    # Assert
    assert check_nodes(neo4j_session, "ModalProxyToken", ["id", "scoped"]) == {
        ("wk-5TgBnHyUjMkIoLpQaZwSxE", False),
        ("wk-6YhNjUmIkOlPaQsWdEfRgT", True),
    }
    assert check_rels(
        neo4j_session,
        "ModalProxyToken",
        "id",
        "ModalWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("wk-5TgBnHyUjMkIoLpQaZwSxE", TEST_WORKSPACE_ID),
        ("wk-6YhNjUmIkOlPaQsWdEfRgT", TEST_WORKSPACE_ID),
    }


@patch.object(
    cartography.intel.modal.environment_roles,
    "get_environment_roles",
    return_value=tests.data.modal.identity.MODAL_ENVIRONMENT_ROLE_PRINCIPALS,
)
def test_load_modal_environment_roles(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_environments(neo4j_session)
    _ensure_local_neo4j_has_test_members(neo4j_session)
    _ensure_local_neo4j_has_test_service_users(neo4j_session)
    params = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": TEST_WORKSPACE_ID,
        "ENVIRONMENT_ID": TEST_ENVIRONMENT_ID,
    }

    # Act
    asyncio.run(
        cartography.intel.modal.environment_roles.sync(
            neo4j_session, MagicMock(), params
        )
    )

    # Assert
    assert check_nodes(neo4j_session, "ModalEnvironmentRole", ["name", "scope"]) == {
        ("viewer", "environment"),
        ("contributor", "environment"),
        ("no-access", "environment"),
    }
    # Both principal kinds bind through the same canonical HAS_ROLE edge.
    assert check_rels(
        neo4j_session,
        "ModalUser",
        "display_name",
        "ModalEnvironmentRole",
        "name",
        "HAS_ROLE",
    ) == {
        ("alice", "contributor"),
        ("bob", "viewer"),
    }
    assert check_rels(
        neo4j_session,
        "ModalServiceUser",
        "name",
        "ModalEnvironmentRole",
        "name",
        "HAS_ROLE",
    ) == {("ci-bot", "contributor")}
