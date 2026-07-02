from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.queries
from tests.data.databricks.queries import DATABRICKS_QUERIES
from tests.data.databricks.queries import DATABRICKS_QUERY_ID
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


def _ensure_local_neo4j_has_test_queries(neo4j_session):
    cartography.intel.databricks.queries.load_queries(
        neo4j_session,
        cartography.intel.databricks.queries.transform(
            DATABRICKS_QUERIES, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.queries,
    "get",
    return_value=DATABRICKS_QUERIES,
)
def test_load_databricks_queries(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_warehouses(neo4j_session)

    cartography.intel.databricks.queries.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksQuery",
        ["id", "display_name", "owner_user_name", "run_as_mode"],
    ) == {
        (
            scoped(DATABRICKS_QUERY_ID),
            "carto-test-query",
            "jeremy@subimage.io",
            "OWNER",
        ),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksQuery",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(scoped(DATABRICKS_QUERY_ID), DATABRICKS_WORKSPACE_ID)}

    assert check_rels(
        neo4j_session,
        "DatabricksQuery",
        "id",
        "DatabricksSqlWarehouse",
        "id",
        "USES_WAREHOUSE",
        rel_direction_right=True,
    ) == {(scoped(DATABRICKS_QUERY_ID), scoped(DATABRICKS_WAREHOUSE_ID))}
