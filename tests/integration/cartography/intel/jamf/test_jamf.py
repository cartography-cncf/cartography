from unittest.mock import patch

import cartography.intel.jamf.computers
from cartography.intel.jamf.computers import sync
from tests.data.jamf.computers import GROUPS
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_JAMF_URI = "https://test.jamfcloud.com"
TEST_JAMF_USER = "test_user"
TEST_JAMF_PASSWORD = "test_password"


@patch.object(
    cartography.intel.jamf.computers,
    "get_computer_groups",
    return_value=GROUPS,
)
def test_sync(mock_get_computer_groups, neo4j_session):
    """
    Ensure that the main sync function orchestrates the Jamf sync correctly.
    """
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    sync(
        neo4j_session,
        TEST_JAMF_URI,
        TEST_JAMF_USER,
        TEST_JAMF_PASSWORD,
        common_job_parameters,
    )

    # Assert - JamfComputerGroup nodes exist with expected properties
    assert check_nodes(
        neo4j_session,
        "JamfComputerGroup",
        ["id", "name", "is_smart"],
    ) == {
        (123, "10.13.6", True),
        (234, "10.14 and Above", True),
        (345, "10.14.6", True),
    }
