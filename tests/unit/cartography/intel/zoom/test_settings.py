from copy import deepcopy
from typing import Any
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.settings import get
from cartography.intel.zoom.settings import sync
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
    assert record["private_chat"] is False
    assert record["allow_participants_to_rename"] is False
    assert record["auto_delete_cloud_recordings"] is True
    assert record["auto_delete_cloud_recordings_days"] == 90
    assert record["waiting_room_scope"] == 1
    assert record["sign_again_period_for_inactivity_on_client"] == 30
    assert record["sign_again_period_for_inactivity_on_web"] == 0
    assert record["two_factor_auth_group_ids"] is None
    assert all(
        value is None or isinstance(value, (str, bool, int))
        for value in record.values()
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
    assert records[1]["private_chat"] is True
    assert records[1]["auto_delete_cloud_recordings"] is True
    # Lock endpoints return flags only, never configured values.
    assert records[1]["auto_delete_cloud_recordings_days"] is None
    assert records[1]["waiting_room_scope"] is None
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


def test_transform_keeps_two_factor_group_and_role_ids() -> None:
    # Arrange
    responses = deepcopy(SETTINGS_RESPONSES)
    security = responses["security"]["security"]
    security["sign_in_with_two_factor_auth"] = "group"
    security["sign_in_with_two_factor_auth_groups"] = ["group-one", "group-two"]
    security["sign_in_with_two_factor_auth_roles"] = []

    # Act
    configured = transform(
        responses, "account-one", "account", "account-one", "configured"
    )
    locked = transform(responses, "account-one", "account", "account-one", "locked")

    # Assert
    assert configured["sign_in_with_two_factor_auth"] == "group"
    assert configured["two_factor_auth_group_ids"] == ["group-one", "group-two"]
    assert configured["two_factor_auth_role_ids"] == []
    assert locked["two_factor_auth_group_ids"] is None


@pytest.mark.parametrize(  # type: ignore[misc]
    "field,path,value",
    [
        ("auto_delete_cloud_recordings_days", ("default", "recording"), "90"),
        ("waiting_room_scope", ("meeting_security", "meeting_security"), True),
        (
            "two_factor_auth_group_ids",
            ("security", "security"),
            ["group-one", 2],
        ),
    ],
)
def test_transform_rejects_malformed_non_boolean_values(
    field: str, path: tuple[str, str], value: Any
) -> None:
    # Arrange
    responses = deepcopy(SETTINGS_RESPONSES)
    section = responses[path[0]][path[1]]
    if field == "waiting_room_scope":
        section["waiting_room_settings"][
            "participants_to_place_in_waiting_room"
        ] = value
    elif field == "two_factor_auth_group_ids":
        section["sign_in_with_two_factor_auth_groups"] = value
    else:
        section["auto_delete_cmr_days"] = value

    # Act and assert
    with pytest.raises(ValueError, match=field):
        transform(responses, "account-one", "account", "account-one", "configured")


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


def test_settings_missing_scope_skips_later_owners_but_not_other_kinds() -> None:
    # Arrange
    client = MagicMock(spec=ZoomClient)
    client.session = MagicMock()
    client.fork.return_value = client
    denied = requests.Response()
    denied.status_code = 400
    denied._content = (
        b'{"code":4711,"message":"Invalid access token, does not contain '
        b'scopes:[group:read:settings:admin]."}'
    )

    def response(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if path.startswith("/groups/") and path.endswith("/settings"):
            raise requests.HTTPError(response=denied)
        return {}

    client.get.side_effect = response
    groups = [{"id": "group-one"}, {"id": "group-two"}]

    # Act
    with patch("cartography.intel.zoom.settings.load") as mocked_load:
        sync(MagicMock(), client, "account-one", 1, [], groups)

    # Assert
    # Concurrent workers share the cache, so at most one read per worker can
    # race past it; the denial is never retried after it is cached.
    paths = [args.args[0] for args in client.get.call_args_list]
    denied_reads = paths.count("/groups/group-one/settings") + paths.count(
        "/groups/group-two/settings"
    )
    assert denied_reads in (1, 2)
    assert paths.count("/groups/group-one/lock_settings") == 2
    assert paths.count("/groups/group-two/lock_settings") == 2
    # One batched write: both account kinds and both group locks.
    mocked_load.assert_called_once()
    assert len(mocked_load.call_args.args[2]) == 4

    # Act: a later sync receives a fresh cache and can retry the denied surface.
    with patch("cartography.intel.zoom.settings.load"):
        sync(MagicMock(), client, "account-one", 2, [], groups)

    # Assert
    paths = [args.args[0] for args in client.get.call_args_list]
    assert (
        paths.count("/groups/group-one/settings")
        + paths.count("/groups/group-two/settings")
        > denied_reads
    )
