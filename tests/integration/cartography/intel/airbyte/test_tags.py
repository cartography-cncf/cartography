from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.airbyte.tags
import tests.data.airbyte.tags
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


def _ensure_local_neo4j_has_test_tags(neo4j_session):
    cartography.intel.airbyte.tags.load_tags(
        neo4j_session,
        tests.data.airbyte.tags.AIRBYTE_TAGS,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.airbyte.tags,
    "get",
    return_value=tests.data.airbyte.tags.AIRBYTE_TAGS,
)
def test_load_airbyte_tags(mock_api, neo4j_session):
    """
    Ensure that tags actually get loaded
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
    cartography.intel.airbyte.tags.sync(
        neo4j_session,
        api_session,
        TEST_ORG_ID,
        workspace_ids,
        common_job_parameters,
    )

    # Assert Tags exist
    expected_nodes = {
        ("f367d42e-4987-41af-9388-c96f6237a798", "sensitive", "75DCFF"),
    }
    assert (
        check_nodes(neo4j_session, "AirbyteTag", ["id", "name", "color"])
        == expected_nodes
    )

    # Assert Tags are connected to the organization
    expected_rels = {
        ("f367d42e-4987-41af-9388-c96f6237a798", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteTag",
            "id",
            "AirbyteOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert tags are connected to the workspace
    # Assert workspaces are connected to the organization
    expected_rels = {
        (
            "e4388e31-9c21-461b-9b5d-1905ca28c599",
            "f367d42e-4987-41af-9388-c96f6237a798",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteWorkspace",
            "id",
            "AirbyteTag",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_rels
    )
