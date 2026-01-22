# Test application data
from typing import Any

APPLICATION_ID_1 = "microsoft:office_365"
APPLICATION_ID_2 = "google:chrome"
APPLICATION_ID_3 = "adobe:photoshop"

# Test application version IDs
APP_VERSION_ID_1 = "microsoft:office_365:2021.16.54"
APP_VERSION_ID_2 = "microsoft:office_365:2021.16.52"
APP_VERSION_ID_3 = "google:chrome:119.0.6045.105"
APP_VERSION_ID_4 = "adobe:photoshop:2023.24.1"

# Test agent UUIDs for relationships
AGENT_UUID_1 = "uuid-123-456-789"
AGENT_UUID_2 = "uuid-456-789-123"
AGENT_UUID_3 = "uuid-789-123-456"

# Raw application data from API
APPLICATIONS_DATA = [
    {
        "applicationName": "Office 365",
        "applicationVendor": "Microsoft",
    },
    {
        "applicationName": "Chrome",
        "applicationVendor": "Google",
    },
    {
        "applicationName": "Photoshop",
        "applicationVendor": "Adobe",
    },
]

# Raw application installs data from API
APPLICATION_INSTALLS_DATA = [
    {
        "applicationName": "Office 365",
        "applicationVendor": "Microsoft",
        "version": "2021.16.54",
        "endpointUuid": AGENT_UUID_1,
        "applicationInstallationPath": "/Applications/Microsoft Office 365",
        "applicationInstallationDate": "2023-01-15T10:30:00Z",
    },
    {
        "applicationName": "Office 365",
        "applicationVendor": "Microsoft",
        "version": "2021.16.52",
        "endpointUuid": AGENT_UUID_2,
        "applicationInstallationPath": "/Applications/Microsoft Office 365",
        "applicationInstallationDate": "2023-01-10T14:22:00Z",
    },
    {
        "applicationName": "Chrome",
        "applicationVendor": "Google",
        "version": "119.0.6045.105",
        "endpointUuid": AGENT_UUID_1,
        "applicationInstallationPath": "/Applications/Google Chrome.app",
        "applicationInstallationDate": "2023-02-20T16:45:00Z",
    },
    {
        "applicationName": "Photoshop",
        "applicationVendor": "Adobe",
        "version": "2023.24.1",
        "endpointUuid": AGENT_UUID_3,
        "applicationInstallationPath": "/Applications/Adobe Photoshop 2023",
        "applicationInstallationDate": "2023-03-01T09:15:00Z",
    },
]

# Test data with minimal fields only
APPLICATIONS_DATA_MINIMAL = [
    {
        "applicationName": "Minimal App",
        "applicationVendor": "Test Vendor",
        # All other fields missing - should be handled gracefully
    },
]

APPLICATION_INSTALLS_DATA_MINIMAL = [
    {
        "applicationName": "Minimal App",
        "applicationVendor": "Test Vendor",
        "version": "1.0.0",
        "endpointUuid": AGENT_UUID_1,
        # Missing optional fields
    },
]

# Test data with missing required fields (for error testing)
APPLICATIONS_DATA_MISSING_NAME = [
    {
        "applicationVendor": "Test Vendor",
        # Missing applicationName
    },
]

APPLICATIONS_DATA_MISSING_VENDOR = [
    {
        "applicationName": "Test App",
        # Missing applicationVendor
    },
]

APPLICATION_INSTALLS_DATA_MISSING_VERSION = [
    {
        "applicationName": "Test App",
        "applicationVendor": "Test Vendor",
        "endpointUuid": AGENT_UUID_1,
        # Missing version
    },
]

APPLICATION_INSTALLS_DATA_MISSING_NAME = [
    {
        "applicationVendor": "Test Vendor",
        "version": "1.0.0",
        "endpointUuid": AGENT_UUID_1,
        # Missing applicationName
    },
]

APPLICATION_INSTALLS_DATA_MISSING_VENDOR = [
    {
        "applicationName": "Test App",
        "version": "1.0.0",
        "endpointUuid": AGENT_UUID_1,
        # Missing applicationVendor
    },
]

# Mock API responses
MOCK_APPLICATIONS_API_RESPONSE = APPLICATIONS_DATA

MOCK_APPLICATION_INSTALLS_API_RESPONSE = APPLICATION_INSTALLS_DATA

MOCK_APPLICATIONS_API_RESPONSE_EMPTY: list[dict[str, Any]] = []

MOCK_APPLICATION_INSTALLS_API_RESPONSE_EMPTY: list[dict[str, Any]] = []

# Account ID for testing relationships
TEST_ACCOUNT_ID = "test-s1-account-123"

# Common job parameters for testing
TEST_UPDATE_TAG = 123456789
TEST_API_URL = "https://test-api.sentinelone.net"
TEST_API_TOKEN = "test-api-token"

TEST_COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "API_URL": TEST_API_URL,
    "API_TOKEN": TEST_API_TOKEN,
    "S1_ACCOUNT_ID": TEST_ACCOUNT_ID,
}
