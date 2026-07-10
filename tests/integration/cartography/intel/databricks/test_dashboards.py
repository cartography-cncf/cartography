from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.dashboards
from tests.data.databricks.dashboards import DATABRICKS_LAKEVIEW_DASHBOARDS
from tests.data.databricks.dashboards import DATABRICKS_LEGACY_DASHBOARDS
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
_LAKEVIEW_ID = "01f175a4ac071e099d6cc5ce1c8ba9fb"
_LEGACY_ID = "9a1c2b3d-legacy-4567-89ab-cdef01234567"


@patch.object(
    cartography.intel.databricks.dashboards,
    "get_legacy",
    return_value=DATABRICKS_LEGACY_DASHBOARDS,
)
@patch.object(
    cartography.intel.databricks.dashboards,
    "get_lakeview",
    return_value=DATABRICKS_LAKEVIEW_DASHBOARDS,
)
def test_load_databricks_dashboards(mock_lakeview, mock_legacy, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_warehouses(neo4j_session)

    cartography.intel.databricks.dashboards.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    # Both Lakeview and legacy dashboards land as one node type, discriminated
    # by dashboard_type; legacy carries an owner and no warehouse.
    assert check_nodes(
        neo4j_session,
        "DatabricksDashboard",
        ["id", "display_name", "dashboard_type", "owner_user_name"],
    ) == {
        (scoped(_LAKEVIEW_ID), "carto-test-dashboard", "LAKEVIEW", None),
        (scoped(_LEGACY_ID), "legacy-sales-dashboard", "LEGACY", "kunaal@subimage.io"),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksDashboard",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (scoped(_LAKEVIEW_ID), DATABRICKS_WORKSPACE_ID),
        (scoped(_LEGACY_ID), DATABRICKS_WORKSPACE_ID),
    }

    # Only the Lakeview dashboard carries a warehouse binding.
    assert check_rels(
        neo4j_session,
        "DatabricksDashboard",
        "id",
        "DatabricksSqlWarehouse",
        "id",
        "USES_WAREHOUSE",
        rel_direction_right=True,
    ) == {(scoped(_LAKEVIEW_ID), scoped(DATABRICKS_WAREHOUSE_ID))}
