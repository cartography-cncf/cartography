"""Miradore API v1 `ConfigProfile` responses, in the shape xmltodict produces."""

from typing import Any

CONFIG_PROFILES: list[dict[str, Any]] = [
    {
        "ID": "8001",
        "Name": "Baseline passcode policy",
        "ConfigurationType": "Passcode",
        "Description": "Minimum passcode requirements for corporate devices.",
        "OSCategory": "iOS",
        "Status": "Active",
    },
    {
        "ID": "8002",
        "Name": "Corporate Wi-Fi",
        "ConfigurationType": "WiFi",
        "OSCategory": "iOS",
        "Status": "Active",
    },
]
