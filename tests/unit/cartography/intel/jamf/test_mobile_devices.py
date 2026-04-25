from typing import Any
from typing import cast
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from cartography.intel.jamf.mobile_devices import _normalize_mobile_os
from cartography.intel.jamf.mobile_devices import get
from cartography.intel.jamf.mobile_devices import transform
from tests.data.jamf.mobile_devices import MOBILE_DEVICES


@patch("cartography.intel.jamf.mobile_devices.get_paginated_jamf_results")
def test_get_requests_groups_section(
    mock_get_paginated_jamf_results: Mock,
) -> None:
    mock_get_paginated_jamf_results.return_value = []

    get(Mock(), "https://test.jamfcloud.com")

    assert mock_get_paginated_jamf_results.call_args.kwargs["params"] == {
        "section": [
            "GENERAL",
            "HARDWARE",
            "SECURITY",
            "GROUPS",
            "USER_AND_LOCATION",
        ],
    }


def test_transform_requires_mobile_device_id() -> None:
    with pytest.raises(KeyError, match="mobileDeviceId"):
        transform([{"deviceType": "iPhone"}])


def test_normalize_mobile_os() -> None:
    cases = [
        ("iPhone", "iOS"),
        ("iPad", "iPadOS"),
        ("iOS", "iOS"),
        ("tvOS", "tvOS"),
        ("Android", "Android"),
        ("unknown", None),
        (None, None),
    ]

    for device_type, expected_os in cases:
        assert _normalize_mobile_os(device_type) == expected_os


def test_transform_normalizes_mobile_os_family() -> None:
    transformed = transform(cast(list[dict[str, Any]], MOBILE_DEVICES))

    assert transformed == [
        {
            "id": 9001,
            "display_name": "Bart-iPhone-01",
            "managed": True,
            "supervised": True,
            "last_inventory_update_date": "2026-04-16T15:20:00Z",
            "last_enrolled_date": "2025-09-01T08:00:00Z",
            "platform": "iPhone",
            "os": "iOS",
            "os_version": "17.4.1",
            "os_build": "21E236",
            "serial_number": "IPHONESPRING001",
            "model": "iPhone 15",
            "model_identifier": "iPhone15,4",
            "activation_lock_enabled": True,
            "bootstrap_token_escrowed": True,
            "data_protected": True,
            "hardware_encryption": True,
            "jailbreak_detected": False,
            "lost_mode_enabled": False,
            "passcode_compliant": True,
            "passcode_present": True,
            "username": "b.simpson",
            "user_real_name": "Bart Simpson",
            "email": "b.simpson@springfield.example",
            "group_ids": [201],
        },
        {
            "id": 9002,
            "display_name": "Lisa-iPad-01",
            "managed": True,
            "supervised": False,
            "last_inventory_update_date": "2026-04-16T12:20:00Z",
            "last_enrolled_date": "2025-03-15T08:00:00Z",
            "platform": "iPad",
            "os": "iPadOS",
            "os_version": "17.3",
            "os_build": "21D50",
            "serial_number": "IPADSPRING001",
            "model": "iPad Pro",
            "model_identifier": "iPad14,3",
            "activation_lock_enabled": False,
            "bootstrap_token_escrowed": False,
            "data_protected": True,
            "hardware_encryption": True,
            "jailbreak_detected": False,
            "lost_mode_enabled": True,
            "passcode_compliant": False,
            "passcode_present": True,
            "username": "l.simpson",
            "user_real_name": "Lisa Simpson",
            "email": "l.simpson@springfield.example",
            "group_ids": [],
        },
    ]
