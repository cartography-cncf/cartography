from copy import deepcopy
from datetime import datetime
from datetime import timezone
from unittest.mock import MagicMock

import pytest

from cartography.intel.zoom import meetings
from cartography.intel.zoom import recordings
from cartography.intel.zoom.client import ZoomClient
from tests.data.zoom.exposure import MEETING
from tests.data.zoom.exposure import RECORDING
from tests.data.zoom.exposure import RECORDING_SETTINGS


def test_meeting_transform_keeps_protection_but_not_credentials() -> None:
    # Arrange
    raw = deepcopy(MEETING)

    # Act
    data = meetings.transform([raw], "account-a")[0]
    peer = meetings.transform([raw], "account-b")[0]

    # Assert
    assert data["id"] == "account-a:meeting:12345678901"
    assert peer["id"] != data["id"]
    assert data["host_graph_id"] == "account-a:user:user-1"
    assert data["password_protected"] is True
    assert data["waiting_room"] is True
    assert data["meeting_authentication"] is False
    assert data["start_time"] == datetime(2026, 9, 29, 12, tzinfo=timezone.utc)
    assert "synthetic-secret" not in str(data)
    assert not {"join_url", "start_url", "agenda", "password"} & data.keys()


@pytest.mark.parametrize(  # type: ignore[misc]
    "password,expected", [(None, None), ("", False), ("secret", True)]
)
def test_omitted_passcodes_are_unknown(
    password: str | None, expected: bool | None
) -> None:
    # Arrange
    meeting = {**MEETING}
    settings = {**RECORDING_SETTINGS}
    if password is None:
        del meeting["password"]
        del settings["password"]
    else:
        meeting["password"] = password
        settings["password"] = password

    # Act
    meeting_data = meetings.transform([meeting], "account-a")
    recording_data = recordings.transform(
        [{**RECORDING, "settings": settings}], "account-a"
    )

    # Assert
    assert meeting_data[0]["password_protected"] is expected
    assert recording_data[0]["password_protected"] is expected


def test_recording_metadata_excludes_file_access_and_uses_instance_identity() -> None:
    # Arrange
    raw = {**RECORDING, "settings": RECORDING_SETTINGS}

    # Act
    data = recordings.transform([raw, {**raw, "uuid": "second-instance"}], "account-a")

    # Assert
    assert data[0]["id"] != data[1]["id"]
    assert data[0]["meeting_graph_id"] == data[1]["meeting_graph_id"]
    assert data[0]["file_types"] == ["CC", "MP4"]
    assert data[0]["share_recording"] == "publicly"
    assert data[0]["recording_authentication"] is True
    assert "synthetic-secret" not in str(data)
    assert "https://" not in str(data)
    assert (
        not {"recording_files", "share_url", "recording_play_passcode", "password"}
        & data[0].keys()
    )


@pytest.mark.parametrize(  # type: ignore[misc]
    "uuid,encoded",
    [
        ("/a+==", "%252Fa%252B%253D%253D"),
        ("a//b", "a%252F%252Fb"),
        ("a/b+==", "a%2Fb%2B%3D%3D"),
    ],
)
def test_recording_settings_uuid_encoding(uuid: str, encoded: str) -> None:
    # Act and assert
    assert recordings.settings_path(uuid) == f"/meetings/{encoded}/recordings/settings"


def test_lists_are_deduplicated_before_detail_fanout() -> None:
    # Arrange
    client = MagicMock(spec=ZoomClient)
    client.session = MagicMock()
    client.fork.return_value = client
    client.get_paginated.return_value = [MEETING, MEETING]
    client.get.return_value = MEETING

    # Act
    data = meetings.get(client, "user/1")

    # Assert
    assert data == [MEETING]
    client.get_paginated.assert_called_once_with(
        "/users/user%2F1/meetings", "meetings", params={"type": "scheduled"}
    )
    client.get.assert_called_once_with("/meetings/12345678901", None)


def test_recordings_set_bounded_dates_and_exclude_my_notes() -> None:
    # Arrange
    client = MagicMock(spec=ZoomClient)
    client.session = MagicMock()
    client.fork.return_value = client
    client.get_paginated.return_value = [RECORDING, RECORDING]
    client.get.return_value = RECORDING_SETTINGS

    # Act
    data = recordings.get(client, "user-1", 7)

    # Assert
    assert data == [{**RECORDING, "settings": RECORDING_SETTINGS}]
    client.get.assert_called_once_with(
        recordings.settings_path(RECORDING["uuid"]), None
    )
    for call in client.get_paginated.call_args_list:
        assert call.args == ("/users/user-1/recordings", "meetings")
        assert call.kwargs["params"]["recording_source_type"] == "cloud_recording_only"
        start = datetime.fromisoformat(call.kwargs["params"]["from"])
        end = datetime.fromisoformat(call.kwargs["params"]["to"])
        assert 0 <= (end - start).days < 7
