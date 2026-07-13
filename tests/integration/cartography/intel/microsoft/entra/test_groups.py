from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from kiota_abstractions.api_error import APIError
from msgraph.generated.models.o_data_errors.main_error import MainError
from msgraph.generated.models.o_data_errors.o_data_error import ODataError

import cartography.intel.microsoft.entra.groups
from cartography.intel.microsoft.entra.groups import get_group_members
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


class MockPage:
    def __init__(self, value, odata_next_link=None):
        self.value = value
        self.odata_next_link = odata_next_link


def _expired_page_token_error() -> ODataError:
    error = ODataError()
    error.response_status_code = 400
    error.error = MainError()
    error.error.code = "Directory_ExpiredPageToken"
    error.error.message = (
        "The specified page token value has expired and can no longer be "
        "included in your request."
    )
    return error


class MockGroupMembersRequestBuilder:
    def __init__(self, first_page, second_page, recover_on_second_attempt=True):
        self.first_page = first_page
        self.second_page = second_page
        self.recover_on_second_attempt = recover_on_second_attempt
        self.first_page_calls = 0
        self.next_page_calls = 0
        self.expired_token_raised = False

    async def get(self):
        self.first_page_calls += 1
        return self.first_page

    def with_url(self, next_link):
        assert next_link == "next-page"
        return MockGroupMembersNextPageRequestBuilder(self)


class MockGroupMembersNextPageRequestBuilder:
    def __init__(self, parent):
        self.parent = parent

    async def get(self):
        self.parent.next_page_calls += 1
        if (
            not self.parent.expired_token_raised
            or not self.parent.recover_on_second_attempt
        ):
            self.parent.expired_token_raised = True
            raise _expired_page_token_error()
        return self.parent.second_page


class MockGroupsRequestBuilder:
    def __init__(self, members_builder):
        self.members_builder = members_builder

    def by_group_id(self, group_id):
        return MockGroupRequestBuilder(self.members_builder)


class MockGroupRequestBuilder:
    def __init__(self, members_builder):
        self.members = members_builder


class MockGraphClient:
    def __init__(self, members_builder):
        self.groups = MockGroupsRequestBuilder(members_builder)


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


@pytest.mark.asyncio
async def test_get_group_members_restarts_after_expired_page_token():
    first_page = MockPage(
        [
            MOCK_GROUP_MEMBERS["11111111-1111-1111-1111-111111111111"][0],
        ],
        "next-page",
    )
    second_page = MockPage(
        [
            MOCK_GROUP_MEMBERS["11111111-1111-1111-1111-111111111111"][1],
            MOCK_GROUP_MEMBERS["11111111-1111-1111-1111-111111111111"][2],
        ],
    )
    members_builder = MockGroupMembersRequestBuilder(first_page, second_page)
    client = MockGraphClient(members_builder)

    user_ids, group_ids = await get_group_members(
        client,
        "11111111-1111-1111-1111-111111111111",
    )

    assert user_ids == [
        "ae4ac864-4433-4ba6-96a6-20f8cffdadcb",
        "11dca63b-cb03-4e53-bb75-fa8060285550",
    ]
    assert group_ids == ["22222222-2222-2222-2222-222222222222"]
    assert members_builder.first_page_calls == 2
    assert members_builder.next_page_calls == 2


@pytest.mark.asyncio
async def test_get_group_members_does_not_restart_expired_page_token_forever():
    first_page = MockPage(
        [
            MOCK_GROUP_MEMBERS["11111111-1111-1111-1111-111111111111"][0],
        ],
        "next-page",
    )
    second_page = MockPage([])
    members_builder = MockGroupMembersRequestBuilder(
        first_page,
        second_page,
        recover_on_second_attempt=False,
    )
    client = MockGraphClient(members_builder)

    with pytest.raises(ODataError):
        await get_group_members(
            client,
            "11111111-1111-1111-1111-111111111111",
        )

    assert members_builder.first_page_calls == 6
    assert members_builder.next_page_calls == 6


@pytest.mark.asyncio
async def test_get_group_members_returns_empty_for_missing_first_page():
    members_builder = MockGroupMembersRequestBuilder(None, MockPage([]))
    client = MockGraphClient(members_builder)

    user_ids, group_ids = await get_group_members(
        client,
        "11111111-1111-1111-1111-111111111111",
    )

    assert user_ids == []
    assert group_ids == []
    assert members_builder.first_page_calls == 1
    assert members_builder.next_page_calls == 0


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
