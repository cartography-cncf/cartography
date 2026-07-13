from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.data_sources
from tests.data.databricks.data_sources import DATABRICKS_DATA_SOURCES
from tests.data.databricks.sql_warehouses import DATABRICKS_WAREHOUSE_ID
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_sql_warehouses import (
    _ensure_local_neo4j_has_test_warehouses,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
_DATA_SOURCE_ID = "1811cbc7-42e8-46f9-875c-b613109cd172"


@patch.object(
    cartography.intel.databricks.data_sources,
    "get",
    return_value=DATABRICKS_DATA_SOURCES,
)
def test_load_databricks_data_sources(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_warehouses(neo4j_session)

    cartography.intel.databricks.data_sources.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksDataSource",
        ["id", "name", "type", "warehouse_id"],
    ) == {
        (
            scoped(_DATA_SOURCE_ID),
            "Serverless Starter Warehouse",
            "databricks_internal",
            DATABRICKS_WAREHOUSE_ID,
        ),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksDataSource",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(scoped(_DATA_SOURCE_ID), DATABRICKS_WORKSPACE_ID)}

    assert check_rels(
        neo4j_session,
        "DatabricksDataSource",
        "id",
        "DatabricksSqlWarehouse",
        "id",
        "BACKED_BY",
        rel_direction_right=True,
    ) == {(scoped(_DATA_SOURCE_ID), scoped(DATABRICKS_WAREHOUSE_ID))}
