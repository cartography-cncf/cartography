import json

from okta.models.application_json_converter import ApplicationJsonConverter

from cartography.intel.okta import applications
from tests.data.okta.application import APPLICATION_WITH_REDITECT_URIS


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
