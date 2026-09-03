import json

from okta.models.application_json_converter import ApplicationJsonConverter

from cartography.intel.okta import applications
from tests.data.okta.application import ACTIVE_DIRECTORY_APPLICATION
from tests.data.okta.application import APPLICATION_WITH_REDITECT_URIS
from tests.data.okta.application import APPLICATION_WITH_UNKNOWN_SIGN_ON_MODE


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
