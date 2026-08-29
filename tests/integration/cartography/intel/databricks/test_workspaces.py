from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.workspaces
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_workspace(neo4j_session):
    cartography.intel.databricks.workspaces.load_workspaces(
        neo4j_session,
        [DATABRICKS_WORKSPACE],
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.workspaces,
    "get",
    return_value=DATABRICKS_WORKSPACE,
)
def test_load_databricks_workspace(mock_get, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    # Act
    workspace = cartography.intel.databricks.workspaces.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert returned value
    assert workspace["id"] == DATABRICKS_WORKSPACE["id"]

    # Assert workspace node exists with extra label Tenant
    expected_nodes = {
        (
            DATABRICKS_WORKSPACE["id"],
            DATABRICKS_WORKSPACE["host"],
            True,
            730,
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "DatabricksWorkspace",
            ["id", "host", "tokens_enabled", "max_token_lifetime_days"],
        )
        == expected_nodes
    )
    # Tenant ontology label is applied
    assert check_nodes(neo4j_session, "Tenant", ["id"]) == {
        (DATABRICKS_WORKSPACE["id"],)
    }
