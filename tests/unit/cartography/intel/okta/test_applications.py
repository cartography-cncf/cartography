import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from okta.models.application_json_converter import ApplicationJsonConverter

from cartography.intel.okta import applications
from cartography.intel.okta.common import OktaApiError
from tests.data.okta.application import ACTIVE_DIRECTORY_APPLICATION
from tests.data.okta.application import APP_GRANTS
from tests.data.okta.application import APPLICATION_WITH_REDITECT_URIS
from tests.data.okta.application import APPLICATION_WITH_UNKNOWN_SIGN_ON_MODE
from tests.data.okta.application import APPLICATIONS


async def _empty_assignments(*args):
    return []


def test_transform_handles_sdk_344_username_template_and_sparse_settings(
    monkeypatch,
) -> None:
    # Arrange
    application = ApplicationJsonConverter.from_dict(
        json.loads(APPLICATION_WITH_REDITECT_URIS)
    )
    monkeypatch.setattr(
        applications, "_get_application_assigned_users", _empty_assignments
    )
    monkeypatch.setattr(
        applications, "_get_application_assigned_groups", _empty_assignments
    )

    # Act
    result = applications._transform_okta_applications(None, [application])

    # Assert
    assert result[0]["credentials_user_name_template_suffix"] is None
    assert result[0]["settings_app_acs_url"] is None


def test_transform_handles_applications_without_credentials_or_settings(
    monkeypatch,
) -> None:
    """
    An unknown signOnMode yields the base Application class (no credentials, name
    nor settings) and a null one yields ActiveDirectoryApplication (no
    credentials). Neither should abort the sync.
    """
    # Arrange
    applications_list = [
        ApplicationJsonConverter.from_dict(APPLICATION_WITH_UNKNOWN_SIGN_ON_MODE),
        ApplicationJsonConverter.from_dict(ACTIVE_DIRECTORY_APPLICATION),
    ]
    monkeypatch.setattr(
        applications, "_get_application_assigned_users", _empty_assignments
    )
    monkeypatch.setattr(
        applications, "_get_application_assigned_groups", _empty_assignments
    )

    # Act
    result = applications._transform_okta_applications(None, applications_list)
    reply_uris = applications._transform_okta_reply_uris(applications_list)

    # Assert
    assert [app["id"] for app in result] == ["0oaUnknownMode", "0oaActiveDirectory"]
    # The SDK sets an unknown mode to None on the model but preserves the raw
    # value, which must still reach the transform.
    assert result[0]["sign_on_mode"] == "MFA_AS_SERVICE"
    assert result[1]["sign_on_mode"] is None
    assert result[0]["name"] is None
    assert result[0]["credentials_signing_kid"] is None
    assert result[0]["settings_app_url"] is None
    assert result[1]["name"] == "active_directory"
    assert result[1]["credentials_signing_kid"] is None
    assert reply_uris == []


@patch.object(
    applications,
    "_get_application_assigned_groups",
    new_callable=AsyncMock,
)
@patch.object(
    applications,
    "_get_application_assigned_users",
    new_callable=AsyncMock,
)
def test_transform_okta_applications_skips_deleted_app_users(
    mock_get_users: AsyncMock,
    mock_get_groups: AsyncMock,
) -> None:
    # Arrange
    deleted_app = ApplicationJsonConverter.from_dict(
        {**APPLICATION_WITH_UNKNOWN_SIGN_ON_MODE, "id": "deleted-app"}
    )
    live_app = ApplicationJsonConverter.from_dict(
        {**ACTIVE_DIRECTORY_APPLICATION, "id": "live-app"}
    )
    mock_get_users.side_effect = [
        OktaApiError(
            "list_application_users",
            SimpleNamespace(error_code="E0000007"),
        ),
        [],
    ]
    mock_get_groups.return_value = []

    # Act
    result = applications._transform_okta_applications(
        MagicMock(),
        [deleted_app, live_app],
    )

    # Assert: base node for the deleted app is kept; live app still transforms.
    # Group enrichment is skipped for the deleted app (no second fetch).
    assert {app["id"] for app in result} == {"deleted-app", "live-app"}
    assert all("user_id" not in app and "group_id" not in app for app in result)
    assert mock_get_users.await_count == 2
    assert mock_get_groups.await_count == 1
    assert mock_get_groups.await_args is not None
    assert mock_get_groups.await_args.args[1] == "live-app"


@patch.object(
    applications,
    "_get_application_assigned_groups",
    new_callable=AsyncMock,
)
@patch.object(
    applications,
    "_get_application_assigned_users",
    new_callable=AsyncMock,
)
def test_transform_okta_applications_skips_deleted_app_groups(
    mock_get_users: AsyncMock,
    mock_get_groups: AsyncMock,
) -> None:
    # Arrange
    deleted_app = ApplicationJsonConverter.from_dict(
        {**APPLICATION_WITH_UNKNOWN_SIGN_ON_MODE, "id": "deleted-app"}
    )
    live_app = ApplicationJsonConverter.from_dict(
        {**ACTIVE_DIRECTORY_APPLICATION, "id": "live-app"}
    )
    mock_get_users.side_effect = [
        ["user-1"],
        [],
    ]
    mock_get_groups.side_effect = [
        OktaApiError(
            "list_application_group_assignments",
            SimpleNamespace(error_code="E0000007"),
        ),
        [],
    ]

    # Act
    result = applications._transform_okta_applications(
        MagicMock(),
        [deleted_app, live_app],
    )

    # Assert: user enrichment from before the 404 is kept; live app completes.
    assert {app["id"] for app in result} == {"deleted-app", "live-app"}
    deleted_rows = [app for app in result if app["id"] == "deleted-app"]
    assert any(app.get("user_id") == "user-1" for app in deleted_rows)
    assert all("group_id" not in app for app in result)
    assert mock_get_users.await_count == 2
    assert mock_get_groups.await_count == 2


@patch.object(
    applications,
    "_get_application_assigned_users",
    new_callable=AsyncMock,
)
def test_transform_okta_applications_reraises_other_okta_errors_on_users(
    mock_get_users: AsyncMock,
) -> None:
    # Arrange
    application = ApplicationJsonConverter.from_dict(
        APPLICATION_WITH_UNKNOWN_SIGN_ON_MODE
    )
    mock_get_users.side_effect = OktaApiError(
        "list_application_users",
        SimpleNamespace(error_code="E0000011"),
    )

    # Act and assert
    with pytest.raises(OktaApiError):
        applications._transform_okta_applications(MagicMock(), [application])


@patch.object(
    applications,
    "_get_application_assigned_groups",
    new_callable=AsyncMock,
)
@patch.object(
    applications,
    "_get_application_assigned_users",
    new_callable=AsyncMock,
)
def test_transform_okta_applications_reraises_other_okta_errors_on_groups(
    mock_get_users: AsyncMock,
    mock_get_groups: AsyncMock,
) -> None:
    # Arrange
    application = ApplicationJsonConverter.from_dict(
        APPLICATION_WITH_UNKNOWN_SIGN_ON_MODE
    )
    mock_get_users.return_value = []
    mock_get_groups.side_effect = OktaApiError(
        "list_application_group_assignments",
        SimpleNamespace(error_code="E0000011"),
    )

    # Act and assert
    with pytest.raises(OktaApiError):
        applications._transform_okta_applications(MagicMock(), [application])


def test_transform_maps_client_auth_settings_and_granted_scopes(monkeypatch) -> None:
    # Arrange
    applications_list = [
        ApplicationJsonConverter.from_dict(app) for app in APPLICATIONS
    ]
    monkeypatch.setattr(
        applications, "_get_application_assigned_users", _empty_assignments
    )
    monkeypatch.setattr(
        applications, "_get_application_assigned_groups", _empty_assignments
    )

    # Act
    result = applications._transform_okta_applications(
        None,
        applications_list,
        {"0oaService": ["okta.users.read"], "0oaWeb": []},
    )

    # Assert
    assert [
        (
            app["id"],
            app.get("credentials_oauth_client_token_endpoint_auth_method"),
            app.get("settings_oauth_client_dpop_bound_access_tokens"),
            app["granted_scopes"],
        )
        for app in result
    ] == [
        ("0oaService", "private_key_jwt", True, ["okta.users.read"]),
        ("0oaWeb", "client_secret_basic", False, []),
        ("0oaFeatures", None, None, None),
    ]


def test_transform_granted_scopes_keeps_active_grants_sorted() -> None:
    # Arrange
    grants = [
        *APP_GRANTS["0oaService"],
        # A second grant of the same scope, e.g. from a user's consent.
        {**APP_GRANTS["0oaService"][0], "id": "oagDuplicate", "source": "END_USER"},
    ]

    # Act
    scopes = applications._transform_granted_scopes(grants)

    # Assert: the revoked okta.groups.manage grant is dropped.
    assert scopes == ["okta.apps.read", "okta.users.read"]


def test_transform_application_roles_scopes_ids_to_the_app() -> None:
    # Arrange: both apps hold Super Administrator with the assignment ID Okta's
    # API reference derives from the role type; the second also holds a custom
    # role.
    super_admin = {
        "id": "KNKVARKSL5AUITKJJY",
        "label": "Super Administrator",
        "type": "SUPER_ADMIN",
        "status": "ACTIVE",
        "created": "2026-01-05T10:00:00.000Z",
        "lastUpdated": "2026-01-05T10:00:00.000Z",
        "assignmentType": "CLIENT",
    }
    custom_role = {
        "id": "irbCustom",
        "label": "Inventory reader",
        "type": "CUSTOM",
        "status": "ACTIVE",
        "assignmentType": "CLIENT",
        "role": "cr0Inventory",
        "resource-set": "iamInventory",
    }

    # Act
    roles = applications._transform_okta_application_roles(
        [("0oaOne", super_admin), ("0oaTwo", super_admin), ("0oaTwo", custom_role)],
    )

    # Assert
    assert [
        (
            role["id"],
            role["application_id"],
            role["assignment_id"],
            role["role_type"],
            role["role_id"],
            role["resource_set_id"],
        )
        for role in roles
    ] == [
        (
            "0oaOne:KNKVARKSL5AUITKJJY",
            "0oaOne",
            "KNKVARKSL5AUITKJJY",
            "SUPER_ADMIN",
            None,
            None,
        ),
        (
            "0oaTwo:KNKVARKSL5AUITKJJY",
            "0oaTwo",
            "KNKVARKSL5AUITKJJY",
            "SUPER_ADMIN",
            None,
            None,
        ),
        (
            "0oaTwo:irbCustom",
            "0oaTwo",
            "irbCustom",
            "CUSTOM",
            "cr0Inventory",
            "iamInventory",
        ),
    ]


async def _deleted_app(*args):
    raise OktaApiError("raw request", SimpleNamespace(error_code="E0000007"))


def test_get_application_roles_skips_an_app_deleted_during_sync(monkeypatch) -> None:
    # Arrange
    application = ApplicationJsonConverter.from_dict(APPLICATIONS[0])
    monkeypatch.setattr(applications, "collect_raw_paginated", _deleted_app)

    # Act
    roles = asyncio.run(applications._get_application_roles(MagicMock(), application))

    # Assert
    assert roles == []


def test_get_application_grants_skips_an_app_deleted_during_sync(monkeypatch) -> None:
    # Arrange
    monkeypatch.setattr(applications, "collect_raw_paginated", _deleted_app)

    # Act
    grants = asyncio.run(applications._get_application_grants(MagicMock(), "0oaWeb"))

    # Assert: None, so the app's granted scopes stay unknown rather than empty.
    assert grants is None
