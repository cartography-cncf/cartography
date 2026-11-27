import json
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest
from neo4j.time import DateTime

from cartography.rules.formatters import to_serializable


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
            "2026-01-02T03:04:05+00:00",
        ),
        (
            datetime(
                2026, 1, 2, 3, 4, 5, 123456, timezone(timedelta(hours=5, minutes=30))
            ),
            "2026-01-02T03:04:05.123456+05:30",
        ),
        (
            datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone(-timedelta(hours=7))),
            "2026-01-02T03:04:05-07:00",
        ),
        (datetime(2026, 1, 2, 3, 4, 5), "2026-01-02T03:04:05"),
        (
            DateTime.from_iso_format("2026-01-02T03:04:05.123456789+00:00"),
            "2026-01-02T03:04:05.123456789+00:00",
        ),
        (
            DateTime.from_iso_format("2026-01-02T03:04:05.123456789+05:30"),
            "2026-01-02T03:04:05.123456789+05:30",
        ),
        (
            DateTime(2026, 1, 2, 3, 4, 5, 123456789),
            "2026-01-02T03:04:05.123456789",
        ),
        (None, None),
    ],
    ids=[
        "utc",
        "offset-and-microseconds",
        "negative-offset",
        "naive",
        "neo4j-utc",
        "neo4j-offset",
        "neo4j-naive",
        "null",
    ],
)
def test_to_serializable_nested_datetime(value, expected):
    # Arrange
    data = {"events": [{"at": value}], "name": "example", "count": 2, "enabled": True}

    # Act
    output = json.loads(json.dumps(to_serializable(data)))

    # Assert
    assert output == {
        "events": [{"at": expected}],
        "name": "example",
        "count": 2,
        "enabled": True,
    }
