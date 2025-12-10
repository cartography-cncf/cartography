from unittest.mock import patch

import pytest

from cartography.intel.sentinelone.application import get_application_data
from cartography.intel.sentinelone.application import get_application_installs
from cartography.intel.sentinelone.application import transform_application_versions
from cartography.intel.sentinelone.application import transform_applications
from tests.data.sentinelone.application import AGENT_UUID_1
from tests.data.sentinelone.application import AGENT_UUID_2
from tests.data.sentinelone.application import AGENT_UUID_3
from tests.data.sentinelone.application import APP_VERSION_ID_1
from tests.data.sentinelone.application import APP_VERSION_ID_2
from tests.data.sentinelone.application import APP_VERSION_ID_3
from tests.data.sentinelone.application import APP_VERSION_ID_4
from tests.data.sentinelone.application import APPLICATION_ID_1
from tests.data.sentinelone.application import APPLICATION_ID_2
from tests.data.sentinelone.application import APPLICATION_ID_3
from tests.data.sentinelone.application import APPLICATION_INSTALLS_DATA
from tests.data.sentinelone.application import APPLICATION_INSTALLS_DATA_MINIMAL
from tests.data.sentinelone.application import APPLICATION_INSTALLS_DATA_MISSING_NAME
from tests.data.sentinelone.application import APPLICATION_INSTALLS_DATA_MISSING_VENDOR
from tests.data.sentinelone.application import APPLICATION_INSTALLS_DATA_MISSING_VERSION
from tests.data.sentinelone.application import APPLICATIONS_DATA
from tests.data.sentinelone.application import APPLICATIONS_DATA_MINIMAL
from tests.data.sentinelone.application import APPLICATIONS_DATA_MISSING_NAME
from tests.data.sentinelone.application import APPLICATIONS_DATA_MISSING_VENDOR
from tests.data.sentinelone.application import TEST_ACCOUNT_ID
from tests.data.sentinelone.application import TEST_API_TOKEN
from tests.data.sentinelone.application import TEST_API_URL


def test_transform_applications():
    """
    Test that transform_applications correctly transforms raw API data with field mapping
    """
    result = transform_applications(APPLICATIONS_DATA)

    assert len(result) == 3

    # Test first application (Office 365)
    app1 = result[0]
    assert app1["id"] == APPLICATION_ID_1
    assert app1["name"] == "Office 365"
    assert app1["vendor"] == "Microsoft"

    # Test second application (Chrome)
    app2 = result[1]
    assert app2["id"] == APPLICATION_ID_2
    assert app2["name"] == "Chrome"
    assert app2["vendor"] == "Google"

    # Test third application (Photoshop)
    app3 = result[2]
    assert app3["id"] == APPLICATION_ID_3
    assert app3["name"] == "Photoshop"
    assert app3["vendor"] == "Adobe"


def test_transform_applications_minimal_fields():
    """
    Test that transform_applications handles minimal fields gracefully
    """
    result = transform_applications(APPLICATIONS_DATA_MINIMAL)

    assert len(result) == 1
    app = result[0]

    # Required fields should be present
    assert app["id"] == "test_vendor:minimal_app"
    assert app["name"] == "Minimal App"
    assert app["vendor"] == "Test Vendor"


def test_transform_applications_missing_required_name():
    """
    Test that transform_applications raises KeyError when applicationName is missing
    """
    with pytest.raises(KeyError):
        transform_applications(APPLICATIONS_DATA_MISSING_NAME)


def test_transform_applications_missing_required_vendor():
    """
    Test that transform_applications raises KeyError when applicationVendor is missing
    """
    with pytest.raises(KeyError):
        transform_applications(APPLICATIONS_DATA_MISSING_VENDOR)


def test_transform_applications_empty_list():
    """
    Test that transform_applications handles empty input list
    """
    result = transform_applications([])
    assert result == []


def test_transform_application_versions():
    """
    Test that transform_application_versions correctly transforms raw API data with field mapping
    """
    result = transform_application_versions(APPLICATION_INSTALLS_DATA)

    assert len(result) == 4

    # Test first application version (Office 365 v2021.16.54)
    version1 = result[0]
    assert version1["id"] == APP_VERSION_ID_1
    assert version1["application_id"] == APPLICATION_ID_1
    assert version1["application_name"] == "Office 365"
    assert version1["application_vendor"] == "Microsoft"
    assert version1["version"] == "2021.16.54"
    assert version1["agent_uuid"] == AGENT_UUID_1
    assert version1["installation_path"] == "/Applications/Microsoft Office 365"
    assert version1["installed_dt"] == "2023-01-15T10:30:00Z"

    # Test second application version (Office 365 v2021.16.52)
    version2 = result[1]
    assert version2["id"] == APP_VERSION_ID_2
    assert (
        version2["application_id"] == APPLICATION_ID_1
    )  # Same application, different version
    assert version2["version"] == "2021.16.52"
    assert version2["agent_uuid"] == AGENT_UUID_2

    # Test third application version (Chrome)
    version3 = result[2]
    assert version3["id"] == APP_VERSION_ID_3
    assert version3["application_id"] == APPLICATION_ID_2
    assert version3["application_name"] == "Chrome"
    assert version3["application_vendor"] == "Google"
    assert version3["version"] == "119.0.6045.105"
    assert version3["agent_uuid"] == AGENT_UUID_1

    # Test fourth application version (Photoshop)
    version4 = result[3]
    assert version4["id"] == APP_VERSION_ID_4
    assert version4["application_id"] == APPLICATION_ID_3
    assert version4["application_name"] == "Photoshop"
    assert version4["application_vendor"] == "Adobe"
    assert version4["version"] == "2023.24.1"
    assert version4["agent_uuid"] == AGENT_UUID_3


def test_transform_application_versions_missing_optional_fields():
    """
    Test that transform_application_versions handles missing optional fields gracefully
    """
    result = transform_application_versions(APPLICATION_INSTALLS_DATA_MINIMAL)

    assert len(result) == 1
    version = result[0]

    # Required fields should be present
    assert version["id"] == "test_vendor:minimal_app:1.0.0"
    assert version["application_id"] == "test_vendor:minimal_app"
    assert version["application_name"] == "Minimal App"
    assert version["application_vendor"] == "Test Vendor"
    assert version["version"] == "1.0.0"
    assert version["agent_uuid"] == AGENT_UUID_1

    # Optional fields should be None
    assert version["installation_path"] is None
    assert version["installed_dt"] is None


def test_transform_application_versions_missing_required_version():
    """
    Test that transform_application_versions handles missing version gracefully by defaulting to 'unknown'
    """
    result = transform_application_versions(APPLICATION_INSTALLS_DATA_MISSING_VERSION)
    assert len(result) == 1
    assert result[0]["version"] == "unknown"
    # Verify that the ID is generated with "unknown" version
    expected_id = "test_vendor:test_app:unknown"
    assert result[0]["id"] == expected_id


def test_transform_application_versions_missing_required_name():
    """
    Test that transform_application_versions raises KeyError when applicationName is missing
    """
    with pytest.raises(KeyError):
        transform_application_versions(APPLICATION_INSTALLS_DATA_MISSING_NAME)


def test_transform_application_versions_missing_required_vendor():
    """
    Test that transform_application_versions raises KeyError when applicationVendor is missing
    """
    with pytest.raises(KeyError):
        transform_application_versions(APPLICATION_INSTALLS_DATA_MISSING_VENDOR)


def test_transform_application_versions_empty_list():
    """
    Test that transform_application_versions handles empty input list
    """
    result = transform_application_versions([])
    assert result == []


def test_application_id_generation():
    """
    Test that application IDs are generated consistently with proper normalization
    """
    result = transform_applications(
        [
            {
                "applicationName": "Test App With Spaces",
                "applicationVendor": "Test Vendor With Spaces",
            },
            {
                "applicationName": "Test-App/With$Special#Characters",
                "applicationVendor": "Test@Vendor&With%Special*Characters",
            },
        ]
    )

    # Verify ID normalization
    assert result[0]["id"] == "test_vendor_with_spaces:test_app_with_spaces"
    assert (
        result[1]["id"]
        == "testvendorwithspecialcharacters:testappwithspecialcharacters"
    )


def test_application_version_id_generation():
    """
    Test that application version IDs are generated consistently with proper normalization
    """
    result = transform_application_versions(
        [
            {
                "applicationName": "Test App",
                "applicationVendor": "Test Vendor",
                "version": "1.2.3-beta",
                "endpointUuid": AGENT_UUID_1,
            },
            {
                "applicationName": "Test App",
                "applicationVendor": "Test Vendor",
                "version": "2.0.0+build.123",
                "endpointUuid": AGENT_UUID_2,
            },
        ]
    )

    # Verify version ID normalization includes version
    assert result[0]["id"] == "test_vendor:test_app:1.2.3-beta"
    assert result[1]["id"] == "test_vendor:test_app:2.0.0+build.123"


@patch("cartography.intel.sentinelone.application.get_paginated_results")
def test_get_application_data(mock_get_paginated_results):
    """
    Test that get_application_data calls API with correct parameters and returns data
    """
    # Mock API response
    mock_get_paginated_results.return_value = APPLICATIONS_DATA

    # Call function
    result = get_application_data(TEST_ACCOUNT_ID, TEST_API_URL, TEST_API_TOKEN)

    # Verify API was called with correct parameters
    mock_get_paginated_results.assert_called_once_with(
        api_url=TEST_API_URL,
        endpoint="/web/api/v2.1/application-management/inventory",
        api_token=TEST_API_TOKEN,
        params={
            "accountIds": TEST_ACCOUNT_ID,
            "limit": 1000,
        },
    )

    # Verify return value
    assert result == APPLICATIONS_DATA


@patch("cartography.intel.sentinelone.application.get_paginated_results")
def test_get_application_data_empty_response(mock_get_paginated_results):
    """
    Test that get_application_data handles empty API response
    """
    # Mock empty API response
    mock_get_paginated_results.return_value = []

    # Call function
    result = get_application_data(TEST_ACCOUNT_ID, TEST_API_URL, TEST_API_TOKEN)

    # Verify return value
    assert result == []


@patch("cartography.intel.sentinelone.application.get_paginated_results")
def test_get_application_installs_empty_inventory(mock_get_paginated_results):
    """
    Test that get_application_installs handles empty application inventory
    """
    # Call function with empty inventory
    result = get_application_installs([], TEST_ACCOUNT_ID, TEST_API_URL, TEST_API_TOKEN)

    # Verify no API calls were made
    mock_get_paginated_results.assert_not_called()

    # Verify empty result
    assert result == []


@patch("cartography.intel.sentinelone.application.get_paginated_results")
def test_get_application_installs_missing_required_fields(mock_get_paginated_results):
    """
    Test that get_application_installs raises KeyError when required fields are missing
    """
    # Create app data missing required fields
    invalid_app_data = [
        {
            "applicationVendor": "Microsoft",
            # Missing applicationName
        }
    ]

    # Should raise KeyError when accessing missing field
    with pytest.raises(KeyError):
        get_application_installs(
            invalid_app_data, TEST_ACCOUNT_ID, TEST_API_URL, TEST_API_TOKEN
        )

    # Verify no API calls were made due to early failure
    mock_get_paginated_results.assert_not_called()


@patch("cartography.intel.sentinelone.application.get_paginated_results")
def test_get_application_installs_missing_vendor(mock_get_paginated_results):
    """
    Test that get_application_installs raises KeyError when applicationVendor is missing
    """
    # Create app data missing vendor
    invalid_app_data = [
        {
            "applicationName": "Test App",
            # Missing applicationVendor
        }
    ]

    # Should raise KeyError when accessing missing field
    with pytest.raises(KeyError):
        get_application_installs(
            invalid_app_data, TEST_ACCOUNT_ID, TEST_API_URL, TEST_API_TOKEN
        )

    # Verify no API calls were made due to early failure
    mock_get_paginated_results.assert_not_called()
