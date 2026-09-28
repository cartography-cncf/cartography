"""Miradore API v1 `Location` responses, in the shape xmltodict produces."""

from typing import Any

LOCATIONS: list[dict[str, Any]] = [
    {
        "ID": "4001",
        "Name": "Finland",
        "FullName": "Finland",
        "Status": "Active",
        "Created": "2023-01-01 00:00:00",
        "Modified": "2023-01-01 00:00:00",
    },
    {
        "ID": "4002",
        "Name": "Helsinki",
        "FullName": "Finland / Helsinki",
        "Status": "Active",
        "Created": "2023-01-02 00:00:00",
        "Modified": "2023-01-02 00:00:00",
        "Parent": {"ID": "4001"},
    },
]
