from copy import deepcopy
from typing import Any
from unittest.mock import call
from unittest.mock import MagicMock

import pytest

from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.settings import get
from cartography.intel.zoom.settings import transform
from tests.data.zoom.settings import LOCKED_SETTINGS_RESPONSES
from tests.data.zoom.settings import SETTINGS_RESPONSES


def test_transform_keeps_only_policy_scalars() -> None:
    # Arrange
    responses = deepcopy(SETTINGS_RESPONSES)

    # Act
    record = transform(responses, "account-one", "user", "user-one", "configured")

    # Assert
    assert record["id"] == "account-one:settings:user:user-one:configured"
    assert record["user_owner_id"] == "account-one:user:user-one"
    assert record["account_owner_id"] is None
    assert record["group_owner_id"] is None
    assert record["pmi_passcode_required"] is True
    assert record["file_transfer"] is False
    assert record["allow_authentication_exception"] is False
    assert record["sign_in_with_two_factor_auth"] == "all"
    assert record["who_can_share_screen"] == "host"
    assert record["encryption_type"] == "e2ee"
    assert record["screen_sharing"] is True
    assert record["recording_embed_passcode_in_link"] is False
    assert all(
        value is None or isinstance(value, (str, bool)) for value in record.values()
    )
    assert "synthetic-secret" not in str(record)
    assert "example.com" not in str(record)
    assert "profile-one" not in str(record)


def test_transform_distinguishes_owner_kind_and_account() -> None:
    # Arrange
    configured = deepcopy(SETTINGS_RESPONSES)
    locked = deepcopy(LOCKED_SETTINGS_RESPONSES)

    # Act
    records = [
        transform(configured, "account-one", "group", "group-one", "configured"),
        transform(locked, "account-one", "group", "group-one", "locked"),
        transform(locked, "account-two", "group", "group-one", "locked"),
        transform(locked, "account-one", "account", "account-one", "locked"),
    ]

    # Assert
    assert len({record["id"] for record in records}) == 4
    assert records[0]["cloud_recording"] is True
    assert records[1]["cloud_recording"] is False
    assert records[1]["meeting_authentication"] is True
    assert records[1]["recording_authentication"] is True
    assert records[1]["encryption_type"] is None
    assert records[1]["group_owner_id"] == "account-one:group:group-one"
    assert records[3]["account_owner_id"] == "account-one"


def test_transform_supports_nested_user_authentication() -> None:
    # Arrange
    responses = deepcopy(SETTINGS_RESPONSES)
    responses["meeting_authentication"] = {
        "authentication_options": {
            "meeting_authentication": {
                "meeting_authentication": True,
                "allow_authentication_exception": False,
            },
        }
    }
    responses["recording_authentication"] = {
        "authentication_options": {
            "recording_authentication": {"recording_authentication": False},
        }
    }

    # Act
    record = transform(responses, "account-one", "user", "user-one", "configured")

    # Assert
    assert record["meeting_authentication"] is True
    assert record["allow_authentication_exception"] is False
    assert record["recording_authentication"] is False


def test_transform_omitted_fields_are_unknown_not_false() -> None:
    # Arrange
    responses: dict[str, dict[str, Any]] = {
        "default": {},
        "meeting_security": {},
        "meeting_authentication": {},
        "recording_authentication": {},
    }

    # Act
    record = transform(responses, "account-one", "group", "group-one", "configured")

    # Assert
    assert record["waiting_room"] is None
    assert record["meeting_authentication"] is None
    assert record["cloud_recording"] is None
    assert record["sign_in_with_two_factor_auth"] is None


@pytest.mark.parametrize("value", ["false", {}, 1])  # type: ignore[misc]
def test_transform_rejects_malformed_policy_values(value: Any) -> None:
    # Arrange
    responses = deepcopy(SETTINGS_RESPONSES)
    responses["meeting_security"]["meeting_security"]["pmi_password"] = value

    # Act and assert
    with pytest.raises(ValueError, match="pmi_passcode_required"):
        transform(responses, "account-one", "account", "account-one", "configured")


@pytest.mark.parametrize(  # type: ignore[misc]
    "scope_type,kind,options",
    [
        (
            "account",
            "configured",
            [
                "meeting_security",
                "meeting_authentication",
                "recording_authentication",
                "security",
            ],
        ),
        (
            "group",
            "configured",
            ["meeting_security", "meeting_authentication", "recording_authentication"],
        ),
        (
            "user",
            "configured",
            ["meeting_security", "meeting_authentication", "recording_authentication"],
        ),
        ("account", "locked", ["meeting_security"]),
        ("group", "locked", ["meeting_security"]),
    ],
)
def test_get_fetches_only_required_response_variants(
    scope_type: str,
    kind: str,
    options: list[str],
) -> None:
    # Arrange
    client = MagicMock(spec=ZoomClient)
    client.get.return_value = {}
    path = "/accounts/me/settings"

    # Act
    responses = get(client, path, scope_type, kind)

    # Assert
    assert client.get.call_args_list == [call(path)] + [
        call(path, {"option": option}) for option in options
    ]
    assert set(responses) == {"default", *options}
