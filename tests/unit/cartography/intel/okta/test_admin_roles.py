from unittest import mock

import pytest
from okta.framework.OktaError import OktaError

from cartography.intel.okta.roles import sync_roles
from cartography.intel.okta.roles import transform_group_roles_data
from cartography.intel.okta.roles import transform_user_roles_data
from cartography.intel.okta.sync_state import OktaSyncState
from cartography.intel.okta.utils import OKTA_RESOURCE_NOT_FOUND_ERROR_CODE
from tests.data.okta.adminroles import LIST_ASSIGNED_GROUP_ROLE_RESPONSE
from tests.data.okta.adminroles import LIST_ASSIGNED_USER_ROLE_RESPONSE


def test_transform_user_roles():
    org_id = "example_org"
    result = transform_user_roles_data(LIST_ASSIGNED_USER_ROLE_RESPONSE, org_id)

    expected = [
        {
            "id": "example_org-APP_ADMIN",
            "label": "Application Administrator",
            "type": "APP_ADMIN",
        },
        {
            "id": "example_org-HELP_DESK_ADMIN",
            "label": "Help Desk Administrator",
            "type": "HELP_DESK_ADMIN",
        },
    ]

    assert result == expected


@mock.patch("cartography.intel.okta.roles.create_api_client")
@mock.patch("cartography.intel.okta.roles._load_group_role")
@mock.patch("cartography.intel.okta.roles._get_group_roles")
def test_sync_roles_skips_deleted_group(
    mock_get_group_roles: mock.MagicMock,
    mock_load_group_role: mock.MagicMock,
    mock_create_api_client: mock.MagicMock,
) -> None:
    """
    A group deleted between listing and role fetch returns a "resource not
    found" OktaError; that group is skipped and the role sync continues.
    """
    sync_state = OktaSyncState(user=None, groups=["deleted-group", "live-group"])
    mock_get_group_roles.side_effect = [
        OktaError({"errorCode": OKTA_RESOURCE_NOT_FOUND_ERROR_CODE}),
        LIST_ASSIGNED_GROUP_ROLE_RESPONSE,
    ]

    sync_roles(mock.MagicMock(), "example_org", 1, "fake-key", sync_state)

    mock_load_group_role.assert_called_once()
    assert mock_load_group_role.call_args.args[1] == "live-group"


@mock.patch("cartography.intel.okta.roles.create_api_client")
@mock.patch("cartography.intel.okta.roles._load_user_role")
@mock.patch("cartography.intel.okta.roles._get_user_roles")
def test_sync_roles_skips_deleted_user(
    mock_get_user_roles: mock.MagicMock,
    mock_load_user_role: mock.MagicMock,
    mock_create_api_client: mock.MagicMock,
) -> None:
    """
    A user deleted between listing and role fetch returns a "resource not
    found" OktaError; that user is skipped and the role sync continues.
    """
    sync_state = OktaSyncState(user=["deleted-user", "live-user"], groups=None)
    mock_get_user_roles.side_effect = [
        OktaError({"errorCode": OKTA_RESOURCE_NOT_FOUND_ERROR_CODE}),
        LIST_ASSIGNED_USER_ROLE_RESPONSE,
    ]

    sync_roles(mock.MagicMock(), "example_org", 1, "fake-key", sync_state)

    mock_load_user_role.assert_called_once()
    assert mock_load_user_role.call_args.args[1] == "live-user"


@mock.patch("cartography.intel.okta.roles.create_api_client")
@mock.patch("cartography.intel.okta.roles._get_group_roles")
def test_sync_roles_reraises_other_okta_errors(
    mock_get_group_roles: mock.MagicMock,
    mock_create_api_client: mock.MagicMock,
) -> None:
    """
    OktaErrors other than "resource not found" must still propagate.
    """
    sync_state = OktaSyncState(user=None, groups=["group-001"])
    mock_get_group_roles.side_effect = OktaError({"errorCode": "E0000011"})

    with pytest.raises(OktaError):
        sync_roles(mock.MagicMock(), "example_org", 1, "fake-key", sync_state)


def test_transform_group_roles():
    org_id = "example_org"
    result = transform_group_roles_data(LIST_ASSIGNED_GROUP_ROLE_RESPONSE, org_id)

    expected = [
        {
            "id": "example_org-APP_ADMIN",
            "label": "Application Administrator",
            "type": "APP_ADMIN",
        },
        {
            "id": "example_org-HELP_DESK_ADMIN",
            "label": "Help Desk Administrator",
            "type": "HELP_DESK_ADMIN",
        },
    ]

    assert result == expected
