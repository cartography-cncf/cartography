from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.okta.groups
from cartography.intel.okta.common import OktaApiError
from tests.data.okta.groups import create_test_group


@patch.object(
    cartography.intel.okta.groups,
    "_get_okta_group_members",
    new_callable=AsyncMock,
)
def test_transform_groups_skips_group_deleted_during_sync(
    mock_get_members: AsyncMock,
) -> None:
    # Arrange
    deleted_group = create_test_group()
    deleted_group.id = "deleted-group"
    live_group = create_test_group()
    live_group.id = "live-group"
    mock_get_members.side_effect = [
        OktaApiError(
            "list_group_users",
            SimpleNamespace(error_code="E0000007"),
        ),
        [],
    ]

    # Act
    result = cartography.intel.okta.groups._transform_okta_groups(
        MagicMock(),
        [deleted_group, live_group],
        [],
    )

    # Assert
    assert {group["id"] for group in result} == {"live-group"}


@patch.object(
    cartography.intel.okta.groups,
    "_get_okta_group_members",
    new_callable=AsyncMock,
)
def test_transform_groups_reraises_other_api_errors(
    mock_get_members: AsyncMock,
) -> None:
    # Arrange
    group = create_test_group()
    mock_get_members.side_effect = OktaApiError(
        "list_group_users",
        SimpleNamespace(error_code="E0000011"),
    )

    # Act and assert
    with pytest.raises(OktaApiError):
        cartography.intel.okta.groups._transform_okta_groups(
            MagicMock(),
            [group],
            [],
        )
