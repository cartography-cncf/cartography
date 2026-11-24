import base64
import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.googleworkspace import start_googleworkspace_ingestion


def _build_oauth_config(scopes: list[str]) -> MagicMock:
    payload = {
        "client_id": "client-id.apps.googleusercontent.com",
        "client_secret": "client-secret",
        "refresh_token": "refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": scopes,
    }
    config = MagicMock()
    config.googleworkspace_auth_method = "oauth"
    config.googleworkspace_config = base64.b64encode(
        json.dumps(payload).encode()
    ).decode()
    config.update_tag = 1234567890
    return config


@pytest.mark.parametrize(
    ("scopes", "expect_oauth_app_sync"),
    [
        (
            [
                "https://www.googleapis.com/auth/admin.directory.customer.readonly",
                "https://www.googleapis.com/auth/admin.directory.user.readonly",
                "https://www.googleapis.com/auth/admin.directory.user.security",
                "https://www.googleapis.com/auth/cloud-identity.groups.readonly",
            ],
            True,
        ),
        (
            [
                "https://www.googleapis.com/auth/admin.directory.customer.readonly",
                "https://www.googleapis.com/auth/admin.directory.user.readonly",
                "https://www.googleapis.com/auth/cloud-identity.groups.readonly",
            ],
            False,
        ),
    ],
    ids=["security-scope-granted", "security-scope-withheld"],
)
@patch("cartography.intel.googleworkspace.oauth_apps.sync_googleworkspace_oauth_apps")
@patch("cartography.intel.googleworkspace.groups.sync_googleworkspace_groups")
@patch(
    "cartography.intel.googleworkspace.users.sync_googleworkspace_users",
    return_value=["user-1"],
)
@patch(
    "cartography.intel.googleworkspace.tenant.sync_googleworkspace_tenant",
    return_value="ABC123CD",
)
@patch("cartography.intel.googleworkspace._initialize_resources")
@patch("google.oauth2.credentials.Credentials.refresh")
def test_oauth_app_sync_requires_security_scope(
    mock_refresh,
    mock_initialize_resources,
    mock_sync_tenant,
    mock_sync_users,
    mock_sync_groups,
    mock_sync_oauth_apps,
    scopes,
    expect_oauth_app_sync,
):
    start_googleworkspace_ingestion(MagicMock(), _build_oauth_config(scopes))

    assert mock_sync_oauth_apps.called is expect_oauth_app_sync
    mock_sync_groups.assert_called_once()


@patch("cartography.intel.googleworkspace.apps_script.sync_googleworkspace_apps_script")
@patch("cartography.intel.googleworkspace.devices.sync_googleworkspace_devices")
@patch("cartography.intel.googleworkspace.groups.sync_googleworkspace_groups")
@patch(
    "cartography.intel.googleworkspace.users.sync_googleworkspace_users",
    return_value=["user-1"],
)
@patch(
    "cartography.intel.googleworkspace.tenant.sync_googleworkspace_tenant",
    return_value="ABC123CD",
)
@patch("cartography.intel.googleworkspace._initialize_resources")
@patch("google.oauth2.credentials.Credentials.refresh")
def test_apps_script_sync_runs_after_groups_and_devices(
    mock_refresh,
    mock_initialize_resources,
    mock_sync_tenant,
    mock_sync_users,
    mock_sync_groups,
    mock_sync_devices,
    mock_sync_apps_script,
):
    # Arrange: record the order of the three syncs
    calls: list[str] = []
    mock_sync_groups.side_effect = lambda *a, **k: calls.append("groups")
    mock_sync_devices.side_effect = lambda *a, **k: calls.append("devices")
    mock_sync_apps_script.side_effect = lambda *a, **k: calls.append("apps_script")
    scopes = [
        "https://www.googleapis.com/auth/admin.directory.customer.readonly",
        "https://www.googleapis.com/auth/admin.directory.user.readonly",
        "https://www.googleapis.com/auth/cloud-identity.groups.readonly",
        "https://www.googleapis.com/auth/cloud-identity.devices.readonly",
    ]

    # Act
    start_googleworkspace_ingestion(MagicMock(), _build_oauth_config(scopes))

    # Assert: the optional Apps Script sync cannot skip groups or devices
    assert calls == ["groups", "devices", "apps_script"]
