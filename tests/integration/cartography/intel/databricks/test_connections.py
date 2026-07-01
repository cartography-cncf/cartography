from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.connections
from tests.data.databricks.connections import DATABRICKS_CONNECTIONS
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
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


def _uc_id(name):
    return f"{DATABRICKS_METASTORE_ID}/{name}"


@patch.object(
    cartography.intel.databricks.connections,
    "get",
    return_value=DATABRICKS_CONNECTIONS,
)
def test_load_databricks_connections(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)

    cartography.intel.databricks.connections.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksConnection",
        ["id", "name", "connection_type", "host"],
    ) == {
        (
            _uc_id("snowflake_prod"),
            "snowflake_prod",
            "SNOWFLAKE",
            "acme.snowflakecomputing.com",
        ),
    }

    # Metastore -> Connection CONTAINS
    assert check_rels(
        neo4j_session,
        "DatabricksMetastore",
        "id",
        "DatabricksConnection",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {(DATABRICKS_METASTORE_ID, _uc_id("snowflake_prod"))}
