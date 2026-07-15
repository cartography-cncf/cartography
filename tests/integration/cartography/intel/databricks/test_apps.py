from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.apps
from tests.data.databricks.apps import DATABRICKS_APPS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.databricks.apps,
    "get",
    return_value=DATABRICKS_APPS,
)
def test_load_databricks_apps(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    cartography.intel.databricks.apps.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksApp",
        ["id", "name", "app_state", "service_principal_client_id"],
    ) == {
        (
            scoped("carto-test-app"),
            "carto-test-app",
            "UNAVAILABLE",
            "7d58cdad-a4d5-4ba1-bd81-15dbde04c88c",
        ),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksApp",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(scoped("carto-test-app"), DATABRICKS_WORKSPACE_ID)}
