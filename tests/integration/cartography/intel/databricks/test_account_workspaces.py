from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.account_workspaces
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.account_workspaces import (
    DATABRICKS_ACCOUNT_WORKSPACE_NODE_IDS,
)
from tests.data.databricks.account_workspaces import DATABRICKS_ACCOUNT_WORKSPACES
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_account_workspaces(neo4j_session):
    cartography.intel.databricks.account_workspaces.load_workspaces(
        neo4j_session,
        cartography.intel.databricks.account_workspaces.transform(
            DATABRICKS_ACCOUNT_WORKSPACES, "cloud.databricks.com"
        ),
        DATABRICKS_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.account_workspaces,
    "get",
    return_value=DATABRICKS_ACCOUNT_WORKSPACES,
)
def test_load_databricks_account_workspaces(mock_get, neo4j_session):
    # Arrange
    api_session = Mock()
    api_session.host = "https://accounts.cloud.databricks.com"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)

    # Act
    node_ids = cartography.intel.databricks.account_workspaces.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    # Assert the returned numeric-id -> node-id mapping
    assert node_ids == DATABRICKS_ACCOUNT_WORKSPACE_NODE_IDS

    # Assert workspace nodes carry the account-API numeric id + name
    assert check_nodes(
        neo4j_session,
        "DatabricksWorkspace",
        ["id", "workspace_id", "workspace_name", "deployment_name"],
    ) == {
        (
            "dbc-aaeaddda-e52f.cloud.databricks.com",
            "1234567890123456",
            "prod",
            "dbc-aaeaddda-e52f",
        ),
        (
            "dbc-bbfbeeeb-f63a.cloud.databricks.com",
            "6543210987654321",
            "staging",
            "dbc-bbfbeeeb-f63a",
        ),
    }

    # Assert Account -> Workspace RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksAccount",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (DATABRICKS_ACCOUNT_ID, "dbc-aaeaddda-e52f.cloud.databricks.com"),
        (DATABRICKS_ACCOUNT_ID, "dbc-bbfbeeeb-f63a.cloud.databricks.com"),
    }


def test_workspace_and_account_paths_keep_each_others_properties(neo4j_session):
    _ensure_local_neo4j_has_test_account(neo4j_session)

    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_account_workspaces(neo4j_session)
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    assert check_nodes(
        neo4j_session,
        "DatabricksWorkspace",
        ["id", "tokens_enabled", "max_token_lifetime_days", "workspace_id"],
    ) == {
        (
            DATABRICKS_WORKSPACE_ID,
            DATABRICKS_WORKSPACE["tokens_enabled"],
            DATABRICKS_WORKSPACE["max_token_lifetime_days"],
            "1234567890123456",
        ),
        ("dbc-bbfbeeeb-f63a.cloud.databricks.com", None, None, "6543210987654321"),
    }
