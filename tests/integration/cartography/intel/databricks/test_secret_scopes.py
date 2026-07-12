from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.secret_scopes
from tests.data.databricks.secret_scopes import DATABRICKS_SECRET_SCOPES
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.databricks.secret_scopes,
    "get",
    return_value=DATABRICKS_SECRET_SCOPES,
)
def test_load_databricks_secret_scopes(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    cartography.intel.databricks.secret_scopes.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksSecretScope",
        ["id", "name", "backend_type", "keyvault_dns_name"],
    ) == {
        (scoped("ci-cd"), "ci-cd", "DATABRICKS", None),
        (
            scoped("azure-kv-backed"),
            "azure-kv-backed",
            "AZURE_KEYVAULT",
            "https://my-kv.vault.azure.net/",
        ),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksSecretScope",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (scoped("ci-cd"), DATABRICKS_WORKSPACE_ID),
        (scoped("azure-kv-backed"), DATABRICKS_WORKSPACE_ID),
    }
