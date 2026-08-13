"""Miradore API v1 `User` responses, in the shape xmltodict produces."""

from typing import Any

USERS: list[dict[str, Any]] = [
    {
        "ID": "2001",
        "Email": "marge.simpson@simpson.corp",
        "Name": "Simpson Marge",
        "Firstname": "Marge",
        "Lastname": "Simpson",
        "PhoneNumber": "+358 50 1234 567",
        "Status": "Active",
        "Source": "AD",
        "Created": "2024-01-05 09:00:00",
        "Modified": "2026-07-01 10:00:00",
    },
    {
        "ID": "2002",
        "Email": "homer.simpson@simpson.corp",
        "Name": "Simpson Homer",
        "Firstname": "Homer",
        "Lastname": "Simpson",
        "Middle": "J",
        "Status": "Retired",
        "Source": "GUI",
        "Created": "2023-03-11 11:00:00",
        "Modified": "2026-04-02 15:30:00",
    },
]
