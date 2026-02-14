from datetime import datetime
from datetime import timedelta
from datetime import timezone

from cartography.intel.santa.events import transform_events
from tests.data.santa.events import EVENT_ROWS


def test_transform_events_builds_app_and_version_records() -> None:
    applications, versions = transform_events(
        EVENT_ROWS,
        source_name="Santa",
        lookback_days=3650,
    )

    assert {app["id"] for app in applications} == {
        "com.apple.terminal",
        "com.google.chrome",
    }

    assert {version["id"] for version in versions} == {
        "com.apple.terminal:2.14",
        "com.google.chrome:124.0",
    }

    terminal_version = next(
        version for version in versions if version["id"] == "com.apple.terminal:2.14"
    )
    assert terminal_version["application_id"] == "com.apple.terminal"
    assert terminal_version["machine_id"] == "C02ABC123"
    assert terminal_version["executed_by_user_id"] == "homer@simpson.corp"


def test_transform_events_respects_lookback_window() -> None:
    now = datetime.now(tz=timezone.utc)
    events = [
        {
            "machine_serial_number": "C02ABC123",
            "bundle_id": "com.apple.Terminal",
            "bundle_name": "Terminal",
            "bundle_version": "2.14",
            "principal_user": {"principal_name": "homer@simpson.corp"},
            "event_time": (now - timedelta(days=1)).isoformat(),
        },
        {
            "machine_serial_number": "C02ABC123",
            "bundle_id": "com.apple.TextEdit",
            "bundle_name": "TextEdit",
            "bundle_version": "1.0",
            "principal_user": {"principal_name": "homer@simpson.corp"},
            "event_time": (now - timedelta(days=30)).isoformat(),
        },
    ]

    applications, versions = transform_events(
        events,
        source_name="Santa",
        lookback_days=7,
    )

    assert applications == [
        {
            "id": "com.apple.terminal",
            "name": "Terminal",
            "identifier": "com.apple.Terminal",
            "source_name": "Santa",
        }
    ]
    assert versions == [
        {
            "id": "com.apple.terminal:2.14",
            "version": "2.14",
            "application_id": "com.apple.terminal",
            "source_name": "Santa",
            "last_seen": events[0]["event_time"],
            "machine_id": "C02ABC123",
            "executed_by_user_id": "homer@simpson.corp",
        }
    ]
