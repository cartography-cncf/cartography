from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.providers
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
from tests.data.databricks.providers import DATABRICKS_PROVIDERS
from tests.data.databricks.providers import PROVIDER_ID
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.integration.cartography.intel.databricks.test_metastores import (
    _ensure_local_neo4j_has_test_metastore,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.databricks.providers,
    "get",
    return_value=DATABRICKS_PROVIDERS,
)
def test_load_databricks_providers(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)

    cartography.intel.databricks.providers.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        DATABRICKS_METASTORE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksProvider",
        ["id", "name", "authentication_type"],
    ) == {(PROVIDER_ID, "acme_data_provider", "TOKEN")}

    assert check_rels(
        neo4j_session,
        "DatabricksProvider",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(PROVIDER_ID, DATABRICKS_WORKSPACE_ID)}

    assert check_rels(
        neo4j_session,
        "DatabricksMetastore",
        "id",
        "DatabricksProvider",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {(DATABRICKS_METASTORE_ID, PROVIDER_ID)}
