"""Miradore API v1 `Organization` responses, in the shape xmltodict produces."""

from typing import Any

ORGANIZATIONS: list[dict[str, Any]] = [
    {
        "ID": "3001",
        "Name": "Simpson Corp",
        "FullName": "Simpson Corp",
        "Status": "Active",
        "Created": "2023-01-01 00:00:00",
        "Modified": "2023-01-01 00:00:00",
    },
    {
        "ID": "3002",
        "Name": "Research and Development",
        "FullName": "Simpson Corp / Research and Development",
        "Status": "Active",
        "Created": "2023-02-01 00:00:00",
        "Modified": "2024-06-01 00:00:00",
        "Parent": {"ID": "3001"},
    },
]
