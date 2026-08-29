from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.instance_pools
from tests.data.databricks.instance_pools import DATABRICKS_INSTANCE_POOLS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.databricks.instance_pools,
    "get",
    return_value=DATABRICKS_INSTANCE_POOLS,
)
def test_load_databricks_instance_pools(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    cartography.intel.databricks.instance_pools.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksInstancePool",
        ["id", "instance_pool_id", "instance_pool_name", "state"],
    ) == {
        (
            scoped("0101-pool-aaaa"),
            "0101-pool-aaaa",
            "shared-warm-pool",
            "ACTIVE",
        ),
        (
            scoped("0101-pool-driver"),
            "0101-pool-driver",
            "driver-only-pool",
            "ACTIVE",
        ),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksInstancePool",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (scoped("0101-pool-aaaa"), DATABRICKS_WORKSPACE_ID),
        (scoped("0101-pool-driver"), DATABRICKS_WORKSPACE_ID),
    }
