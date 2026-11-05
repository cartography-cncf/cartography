from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from okta.models.admin_console_settings import AdminConsoleSettings

from cartography.intel.okta.organization import _get_admin_console_settings


def test_get_admin_console_settings() -> None:
    # Arrange
    okta_client = MagicMock()
    okta_client.get_first_party_app_settings = AsyncMock(
        return_value=(
            AdminConsoleSettings(
                session_idle_timeout_minutes=15,
                session_max_lifetime_minutes=720,
            ),
            None,
            None,
        ),
    )

    # Act
    settings = _get_admin_console_settings(okta_client)

    # Assert
    okta_client.get_first_party_app_settings.assert_awaited_once_with("admin-console")
    assert settings == {
        "admin_console_session_idle_timeout_minutes": 15,
        "admin_console_session_max_lifetime_minutes": 720,
    }


def test_get_admin_console_settings_skips_missing_scope() -> None:
    # Arrange
    okta_client = MagicMock()
    okta_client.get_first_party_app_settings = AsyncMock(
        return_value=(None, None, SimpleNamespace(error_code="E0000006")),
    )

    # Act / Assert
    assert _get_admin_console_settings(okta_client) == {}
