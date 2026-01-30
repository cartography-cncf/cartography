from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.airbyte.workspaces
import tests.data.airbyte.workspaces
from tests.integration.cartography.intel.airbyte.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "31634962-4b3c-4b0c-810d-a2a77d6df222"


def _ensure_local_neo4j_has_test_workspaces(neo4j_session):
    cartography.intel.airbyte.workspaces.load_workspaces(
        neo4j_session,
        tests.data.airbyte.workspaces.AIRBYTE_WORKSPACES,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.airbyte.workspaces,
    "get",
    return_value=tests.data.airbyte.workspaces.AIRBYTE_WORKSPACES,
)
def test_load_airbyte_workspaces(mock_api, neo4j_session):
    """
    Ensure that workspaces actually get loaded
    """
    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_organizations(neo4j_session)

    # Act
    cartography.intel.airbyte.workspaces.sync(
        neo4j_session,
        api_session,
        TEST_ORG_ID,
        common_job_parameters,
    )

    # Assert Workspaces exist
    expected_nodes = {
        ("e4388e31-9c21-461b-9b5d-1905ca28c599", "SpringField Nuclear Plant"),
    }
    assert (
        check_nodes(neo4j_session, "AirbyteWorkspace", ["id", "name"]) == expected_nodes
    )

    # Assert workspaces are connected to the organization
    expected_rels = {
        ("e4388e31-9c21-461b-9b5d-1905ca28c599", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteWorkspace",
            "id",
            "AirbyteOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
