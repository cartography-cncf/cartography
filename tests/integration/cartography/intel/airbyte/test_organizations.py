from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.airbyte.organizations
import tests.data.airbyte.organizations
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "31634962-4b3c-4b0c-810d-a2a77d6df222"


def _ensure_local_neo4j_has_test_organizations(neo4j_session):
    cartography.intel.airbyte.organizations.load_organizations(
        neo4j_session,
        tests.data.airbyte.organizations.AIRBYTE_ORGANIZATIONS,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.airbyte.organizations,
    "get",
    return_value=tests.data.airbyte.organizations.AIRBYTE_ORGANIZATIONS,
)
def test_load_airbyte_organizations(mock_api, neo4j_session):
    """
    Ensure that organizations actually get loaded
    """

    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    cartography.intel.airbyte.organizations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Organizations exist
    expected_nodes = {(TEST_ORG_ID, "Simpson Corp", "admin@simpson.corp")}
    assert (
        check_nodes(neo4j_session, "AirbyteOrganization", ["id", "name", "email"])
        == expected_nodes
    )
