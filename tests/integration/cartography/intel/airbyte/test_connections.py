from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.airbyte.connections
import tests.data.airbyte.connections
import tests.data.airbyte.workspaces
from tests.integration.cartography.intel.airbyte.test_destinations import (
    _ensure_local_neo4j_has_test_destinations,
)
from tests.integration.cartography.intel.airbyte.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.cartography.intel.airbyte.test_sources import (
    _ensure_local_neo4j_has_test_sources,
)
from tests.integration.cartography.intel.airbyte.test_tags import (
    _ensure_local_neo4j_has_test_tags,
)
from tests.integration.cartography.intel.airbyte.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "31634962-4b3c-4b0c-810d-a2a77d6df222"


@patch.object(
    cartography.intel.airbyte.connections,
    "get",
    return_value=tests.data.airbyte.connections.AIRBYTE_CONNECTIONS,
)
def test_load_airbyte_connections(mock_api, neo4j_session):
    """
    Ensure that connections actually get loaded
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
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)
    _ensure_local_neo4j_has_test_tags(neo4j_session)
    _ensure_local_neo4j_has_test_sources(neo4j_session)
    _ensure_local_neo4j_has_test_destinations(neo4j_session)

    # Act
    cartography.intel.airbyte.connections.sync(
        neo4j_session,
        api_session,
        TEST_ORG_ID,
        workspace_ids,
        common_job_parameters,
    )

    # Assert Connections exist
    expected_nodes = {
        ("b9fd93fc-115c-4b5a-a10f-833280713819", "Backup to S3"),
    }
    assert (
        check_nodes(neo4j_session, "AirbyteConnection", ["id", "name"])
        == expected_nodes
    )

    # Assert Streams exist
    expected_nodes = {
        ("b9fd93fc-115c-4b5a-a10f-833280713819_users", "users"),
        ("b9fd93fc-115c-4b5a-a10f-833280713819_issues", "issues"),
    }
    assert check_nodes(neo4j_session, "AirbyteStream", ["id", "name"]) == expected_nodes

    # Assert Connections are linked to Organizations
    expected_rels = {
        ("b9fd93fc-115c-4b5a-a10f-833280713819", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteConnection",
            "id",
            "AirbyteOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
    # Assert Connections are linked to Workspaces
    expected_rels = {
        (
            "b9fd93fc-115c-4b5a-a10f-833280713819",
            "e4388e31-9c21-461b-9b5d-1905ca28c599",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteConnection",
            "id",
            "AirbyteWorkspace",
            "id",
            "CONTAINS",
            rel_direction_right=False,
        )
        == expected_rels
    )
    # Assert Connections are linked to Tags
    expected_rels = {
        (
            "b9fd93fc-115c-4b5a-a10f-833280713819",
            "f367d42e-4987-41af-9388-c96f6237a798",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteConnection",
            "id",
            "AirbyteTag",
            "id",
            "TAGGED",
            rel_direction_right=True,
        )
        == expected_rels
    )
    # Assert Connections are linked to Sources
    expected_rels = {
        (
            "b9fd93fc-115c-4b5a-a10f-833280713819",
            "b626221b-9250-4c8b-8615-653ca7e807ab",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteConnection",
            "id",
            "AirbyteSource",
            "id",
            "SYNC_FROM",
            rel_direction_right=True,
        )
        == expected_rels
    )
    # Assert Connections are linked to Destinations
    expected_rels = {
        ("b9fd93fc-115c-4b5a-a10f-833280713819", "30e064ed-4211-4868-9b8f-e2bbc8f8969a")
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteConnection",
            "id",
            "AirbyteDestination",
            "id",
            "SYNC_TO",
            rel_direction_right=True,
        )
        == expected_rels
    )
    # Assert Streams are linked to Connections
    expected_rels = {
        (
            "b9fd93fc-115c-4b5a-a10f-833280713819_issues",
            "b9fd93fc-115c-4b5a-a10f-833280713819",
        ),
        (
            "b9fd93fc-115c-4b5a-a10f-833280713819_users",
            "b9fd93fc-115c-4b5a-a10f-833280713819",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteStream",
            "id",
            "AirbyteConnection",
            "id",
            "HAS",
            rel_direction_right=False,
        )
        == expected_rels
    )
