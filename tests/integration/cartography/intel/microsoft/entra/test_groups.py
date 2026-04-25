from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from kiota_abstractions.api_error import APIError

import cartography.intel.microsoft.entra.groups
from cartography.intel.microsoft.entra.groups import sync_entra_groups
from cartography.intel.microsoft.entra.users import load_tenant
from cartography.intel.microsoft.entra.users import load_users
from cartography.intel.microsoft.entra.users import transform_users
from tests.data.microsoft.entra.groups import MOCK_DELETED_GROUP
from tests.data.microsoft.entra.groups import MOCK_ENTRA_GROUPS
from tests.data.microsoft.entra.groups import MOCK_ENTRA_GROUPS_WITH_DELETED
from tests.data.microsoft.entra.groups import MOCK_GROUP_MEMBERS
from tests.data.microsoft.entra.groups import TEST_CLIENT_ID
from tests.data.microsoft.entra.groups import TEST_CLIENT_SECRET
from tests.data.microsoft.entra.groups import TEST_TENANT_ID
from tests.data.microsoft.entra.users import MOCK_ENTRA_USERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 1234567890


def mock_get_group_members_side_effect(
    client, group_id: str
) -> tuple[list[str], list[str]]:
    """
    Mock side effect function to return member user IDs and subgroup IDs for a given group.
    """
    members = MOCK_GROUP_MEMBERS[group_id]
    user_ids = [o.id for o in members if o.odata_type == "#microsoft.graph.user"]
    group_ids = [o.id for o in members if o.odata_type == "#microsoft.graph.group"]
    return user_ids, group_ids


def mock_get_group_owners_side_effect(client, group_id: str) -> list[str]:
    """
    Mock side effect function to return owner user IDs for a given group.
    """
    if group_id == "11111111-1111-1111-1111-111111111111":
        return ["ae4ac864-4433-4ba6-96a6-20f8cffdadcb"]
    elif group_id == "22222222-2222-2222-2222-222222222222":
        return ["11dca63b-cb03-4e53-bb75-fa8060285550"]
    else:
        return []


async def _mock_get_entra_groups(client):
    """Mock async generator for get_entra_groups"""
    for group in MOCK_ENTRA_GROUPS:
        yield group


@patch.object(
    cartography.intel.microsoft.entra.groups,
    "get_entra_groups",
    side_effect=_mock_get_entra_groups,
)
@patch.object(
    cartography.intel.microsoft.entra.groups,
    "get_group_members",
    new_callable=AsyncMock,
    side_effect=mock_get_group_members_side_effect,
)
@patch.object(
    cartography.intel.microsoft.entra.groups,
    "get_group_owners",
    new_callable=AsyncMock,
    side_effect=mock_get_group_owners_side_effect,
)
@pytest.mark.asyncio
async def test_sync_entra_groups(
    mock_get_owners, mock_get_members, mock_get_groups, neo4j_session
):
    """Ensure groups and relationships load"""
    # Arrange: load tenant and users
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, TEST_UPDATE_TAG)
    load_users(
        neo4j_session,
        list(transform_users(MOCK_ENTRA_USERS)),
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
    )

    # Act:
    await sync_entra_groups(
        neo4j_session,
        TEST_TENANT_ID,
        TEST_CLIENT_ID,
        TEST_CLIENT_SECRET,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert
    expected_nodes = {
        ("11111111-1111-1111-1111-111111111111", "Security Team"),
        ("22222222-2222-2222-2222-222222222222", "Developers"),
    }
    assert (
        check_nodes(neo4j_session, "EntraGroup", ["id", "display_name"])
        == expected_nodes
    )

    expected_rels = {
        ("11111111-1111-1111-1111-111111111111", TEST_TENANT_ID),
        ("22222222-2222-2222-2222-222222222222", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraGroup",
            "id",
            "EntraTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    expected_membership = {
        (
            "ae4ac864-4433-4ba6-96a6-20f8cffdadcb",
            "11111111-1111-1111-1111-111111111111",
        ),
        (
            "11dca63b-cb03-4e53-bb75-fa8060285550",
            "11111111-1111-1111-1111-111111111111",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraUser",
            "id",
            "EntraGroup",
            "id",
            "MEMBER_OF",
        )
        == expected_membership
    )

    expected_group_membership = {
        ("11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222")
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraGroup",
            "id",
            "EntraGroup",
            "id",
            "MEMBER_OF",
            rel_direction_right=False,
        )
        == expected_group_membership
    )

    expected_ownership = {
        (
            "ae4ac864-4433-4ba6-96a6-20f8cffdadcb",
            "11111111-1111-1111-1111-111111111111",
        ),
        (
            "11dca63b-cb03-4e53-bb75-fa8060285550",
            "22222222-2222-2222-2222-222222222222",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraUser",
            "id",
            "EntraGroup",
            "id",
            "OWNER_OF",
        )
        == expected_ownership
    )


async def _mock_get_entra_groups_with_deleted(client):
    """Mock async generator that includes a group that no longer exists."""
    for group in MOCK_ENTRA_GROUPS_WITH_DELETED:
        yield group


def mock_get_group_owners_404_side_effect(client, group_id: str) -> list[str]:
    """Return owners for valid groups, raise 404 for the deleted group."""
    if group_id == MOCK_DELETED_GROUP.id:
        err = APIError("not found")
        err.response_status_code = 404
        raise err
    return mock_get_group_owners_side_effect(client, group_id)


def mock_get_group_members_404_side_effect(
    client,
    group_id: str,
) -> tuple[list[str], list[str]]:
    """Return members for valid groups, raise 404 for the deleted group."""
    if group_id == MOCK_DELETED_GROUP.id:
        err = APIError("not found")
        err.response_status_code = 404
        raise err
    return mock_get_group_members_side_effect(client, group_id)


@patch.object(
    cartography.intel.microsoft.entra.groups,
    "get_entra_groups",
    side_effect=_mock_get_entra_groups_with_deleted,
)
@patch.object(
    cartography.intel.microsoft.entra.groups,
    "get_group_members",
    new_callable=AsyncMock,
    side_effect=mock_get_group_members_404_side_effect,
)
@patch.object(
    cartography.intel.microsoft.entra.groups,
    "get_group_owners",
    new_callable=AsyncMock,
    side_effect=mock_get_group_owners_404_side_effect,
)
@pytest.mark.asyncio
async def test_sync_entra_groups_skips_404(
    mock_get_owners,
    mock_get_members,
    mock_get_groups,
    neo4j_session,
):
    """Ensure a group that returns 404 on detail fetch is skipped, not crash the sync."""
    # Arrange
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, TEST_UPDATE_TAG)
    load_users(
        neo4j_session,
        list(transform_users(MOCK_ENTRA_USERS)),
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
    )

    # Act — should not raise despite the 404
    await sync_entra_groups(
        neo4j_session,
        TEST_TENANT_ID,
        TEST_CLIENT_ID,
        TEST_CLIENT_SECRET,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert — only the two valid groups are synced; the deleted one is skipped
    expected_nodes = {
        ("11111111-1111-1111-1111-111111111111", "Security Team"),
        ("22222222-2222-2222-2222-222222222222", "Developers"),
    }
    assert (
        check_nodes(neo4j_session, "EntraGroup", ["id", "display_name"])
        == expected_nodes
    )
