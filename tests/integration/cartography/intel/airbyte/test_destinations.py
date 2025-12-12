from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.airbyte.destinations
import tests.data.airbyte.destinations
import tests.data.airbyte.workspaces
from tests.integration.cartography.intel.airbyte.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.cartography.intel.airbyte.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "31634962-4b3c-4b0c-810d-a2a77d6df222"


def _ensure_local_neo4j_has_test_destinations(neo4j_session):
    cartography.intel.airbyte.destinations.load_destinations(
        neo4j_session,
        tests.data.airbyte.destinations.AIRBYTE_DESTINATIONS,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.airbyte.destinations,
    "get",
    return_value=tests.data.airbyte.destinations.AIRBYTE_DESTINATIONS,
)
def test_load_airbyte_destinations(mock_api, neo4j_session):
    """
    Ensure that destinations actually get loaded
    """

    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    workspace_ids = [
        w["workspaceId"] for w in tests.data.airbyte.workspaces.AIRBYTE_WORKSPACES
    ]
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)
    _ensure_local_neo4j_has_test_organizations(neo4j_session)

    # Act
    cartography.intel.airbyte.destinations.sync(
        neo4j_session,
        api_session,
        TEST_ORG_ID,
        workspace_ids,
        common_job_parameters,
    )

    # Assert Destinations exist
    expected_nodes = {
        (
            "30e064ed-4211-4868-9b8f-e2bbc8f8969a",
            "S3",
            "s3",
            "bucket-cartography",
            "af-south-1",
            "https://cellar-c2.services.clever-cloud.com",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "AirbyteDestination",
            ["id", "name", "type", "config_name", "config_region", "config_endpoint"],
        )
        == expected_nodes
    )

    # Assert Destinations are connected to the organization
    expected_rels = {
        ("30e064ed-4211-4868-9b8f-e2bbc8f8969a", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteDestination",
            "id",
            "AirbyteOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert destinations are connected to the workspace
    # Assert workspaces are connected to the organization
    expected_rels = {
        (
            "e4388e31-9c21-461b-9b5d-1905ca28c599",
            "30e064ed-4211-4868-9b8f-e2bbc8f8969a",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteWorkspace",
            "id",
            "AirbyteDestination",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_rels
    )
