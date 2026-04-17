from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.jamf.groups import get
from cartography.intel.jamf.groups import transform


@patch("cartography.intel.jamf.groups.get_paginated_jamf_results")
def test_get_falls_back_to_classic_computer_and_mobile_groups(
    mock_get_paginated_jamf_results: Mock,
) -> None:
    response = requests.Response()
    response.status_code = 404
    err = requests.HTTPError(response=response)
    mock_get_paginated_jamf_results.side_effect = err

    mock_session = Mock()

    with patch(
        "cartography.intel.jamf.groups.call_jamf_api",
        side_effect=[
            {
                "computer_groups": [
                    {"id": 101, "name": "Springfield Managed Macs", "is_smart": True},
                ],
            },
            {
                "mobile_device_groups": [
                    {"id": 201, "name": "Springfield iPhones", "is_smart": False},
                ],
            },
        ],
    ) as mock_call_jamf_api:
        results = get(mock_session, "https://test.jamfcloud.com/JSSResource")

    assert results == [
        {
            "groupDescription": None,
            "groupJamfProId": 101,
            "groupName": "Springfield Managed Macs",
            "groupType": "COMPUTER",
            "membershipCount": None,
            "smart": True,
        },
        {
            "groupDescription": None,
            "groupJamfProId": 201,
            "groupName": "Springfield iPhones",
            "groupType": "MOBILE",
            "membershipCount": None,
            "smart": False,
        },
    ]
    assert [call.args[0] for call in mock_call_jamf_api.call_args_list] == [
        "/computergroups",
        "/mobiledevicegroups",
    ]


@patch("cartography.intel.jamf.groups.get_paginated_jamf_results")
def test_get_legacy_fallback_skips_mobile_groups_when_classic_endpoint_missing(
    mock_get_paginated_jamf_results: Mock,
) -> None:
    response = requests.Response()
    response.status_code = 404
    err = requests.HTTPError(response=response)
    mock_get_paginated_jamf_results.side_effect = err

    mobile_response = requests.Response()
    mobile_response.status_code = 404
    mobile_err = requests.HTTPError(response=mobile_response)

    mock_session = Mock()

    with patch(
        "cartography.intel.jamf.groups.call_jamf_api",
        side_effect=[
            {
                "computer_groups": [
                    {"id": 101, "name": "Springfield Managed Macs", "is_smart": True},
                ],
            },
            mobile_err,
        ],
    ):
        results = get(mock_session, "https://test.jamfcloud.com/JSSResource")

    assert results == [
        {
            "groupDescription": None,
            "groupJamfProId": 101,
            "groupName": "Springfield Managed Macs",
            "groupType": "COMPUTER",
            "membershipCount": None,
            "smart": True,
        },
    ]


def test_transform_requires_group_id() -> None:
    with pytest.raises(KeyError, match="groupJamfProId"):
        transform(
            [
                {
                    "groupName": "Springfield Managed Macs",
                    "groupType": "COMPUTER",
                },
            ],
        )
