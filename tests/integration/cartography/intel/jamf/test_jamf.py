from unittest.mock import patch

import cartography.intel.jamf.computers
from cartography.intel.jamf.computers import sync
from tests.data.jamf.computers import GROUPS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JAMF_URI = "https://test.jamfcloud.com"
TEST_JAMF_USER = "test_user"
TEST_JAMF_PASSWORD = "test_password"


@patch.object(
    cartography.intel.jamf.computers,
    "get",
    return_value=GROUPS,
)
def test_sync(mock_get, neo4j_session):
    """
    Ensure that the main sync function orchestrates the Jamf sync correctly.
    """
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_JAMF_URI,
    }

    # Act
    sync(
        neo4j_session,
        TEST_JAMF_URI,
        TEST_JAMF_USER,
        TEST_JAMF_PASSWORD,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - JamfTenant node exists
    assert check_nodes(
        neo4j_session,
        "JamfTenant",
        ["id"],
    ) == {
        (TEST_JAMF_URI,),
    }

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

    # Assert - Relationships exist between tenant and computer groups
    assert check_rels(
        neo4j_session,
        "JamfTenant",
        "id",
        "JamfComputerGroup",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_JAMF_URI, 123),
        (TEST_JAMF_URI, 234),
        (TEST_JAMF_URI, 345),
    }
