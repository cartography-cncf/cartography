from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.sql_warehouses
from tests.data.databricks.sql_warehouses import DATABRICKS_SQL_WAREHOUSES
from tests.data.databricks.sql_warehouses import DATABRICKS_WAREHOUSE_ID
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_warehouses(neo4j_session):
    cartography.intel.databricks.sql_warehouses.load_warehouses(
        neo4j_session,
        cartography.intel.databricks.sql_warehouses.transform(
            DATABRICKS_SQL_WAREHOUSES, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.sql_warehouses,
    "get",
    return_value=DATABRICKS_SQL_WAREHOUSES,
)
def test_load_databricks_sql_warehouses(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    cartography.intel.databricks.sql_warehouses.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksSqlWarehouse",
        ["id", "warehouse_id", "name", "enable_serverless_compute", "warehouse_type"],
    ) == {
        (
            scoped(DATABRICKS_WAREHOUSE_ID),
            DATABRICKS_WAREHOUSE_ID,
            "Serverless Starter Warehouse",
            True,
            "PRO",
        ),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksSqlWarehouse",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(scoped(DATABRICKS_WAREHOUSE_ID), DATABRICKS_WORKSPACE_ID)}
