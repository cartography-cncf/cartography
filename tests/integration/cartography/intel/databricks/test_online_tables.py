from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.online_tables
import cartography.intel.databricks.tables
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
from tests.data.databricks.online_tables import DATABRICKS_ONLINE_TABLES
from tests.data.databricks.tables import DATABRICKS_TABLES
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


def _uc_id(full_name):
    return f"{DATABRICKS_METASTORE_ID}/{full_name}"


@patch.object(
    cartography.intel.databricks.online_tables,
    "get",
    return_value=DATABRICKS_ONLINE_TABLES,
)
def test_load_databricks_online_tables(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)
    cartography.intel.databricks.tables.load_tables(
        neo4j_session,
        cartography.intel.databricks.tables.transform(DATABRICKS_TABLES),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )

    cartography.intel.databricks.online_tables.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksOnlineTable",
        ["id", "name", "detailed_state"],
    ) == {
        (
            _uc_id("prod.finance.customers_online"),
            "prod.finance.customers_online",
            "ONLINE_NO_PENDING_UPDATE",
        ),
    }

    # OnlineTable -> source DatabricksTable SOURCED_FROM
    assert check_rels(
        neo4j_session,
        "DatabricksOnlineTable",
        "id",
        "DatabricksTable",
        "id",
        "SOURCED_FROM",
        rel_direction_right=True,
    ) == {
        (
            _uc_id("prod.finance.customers_online"),
            _uc_id("prod.finance.customers"),
        )
    }
