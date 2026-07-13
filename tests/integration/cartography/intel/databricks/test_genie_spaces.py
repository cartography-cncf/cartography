from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.genie_spaces
from tests.data.databricks.genie_spaces import DATABRICKS_GENIE_SPACES
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
_SPACE_ID = "01f1749e632b10acab9da9a9ca010dfb"


@patch.object(
    cartography.intel.databricks.genie_spaces,
    "get",
    return_value=DATABRICKS_GENIE_SPACES,
)
def test_load_databricks_genie_spaces(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_warehouses(neo4j_session)

    cartography.intel.databricks.genie_spaces.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksGenieSpace",
        ["id", "title", "warehouse_id"],
    ) == {
        (scoped(_SPACE_ID), "Bakehouse Sales Starter Space", DATABRICKS_WAREHOUSE_ID),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksGenieSpace",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(scoped(_SPACE_ID), DATABRICKS_WORKSPACE_ID)}

    assert check_rels(
        neo4j_session,
        "DatabricksGenieSpace",
        "id",
        "DatabricksSqlWarehouse",
        "id",
        "USES_WAREHOUSE",
        rel_direction_right=True,
    ) == {(scoped(_SPACE_ID), scoped(DATABRICKS_WAREHOUSE_ID))}
