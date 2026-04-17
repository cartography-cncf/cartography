from unittest.mock import Mock
from unittest.mock import patch

import pytest

from cartography.intel.jamf.mobile_devices import get
from cartography.intel.jamf.mobile_devices import transform


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
