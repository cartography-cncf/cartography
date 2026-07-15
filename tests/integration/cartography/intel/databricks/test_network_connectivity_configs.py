from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.network_connectivity_configs
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.network_connectivity_configs import (
    DATABRICKS_NETWORK_CONNECTIVITY_CONFIGS,
)
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.databricks.network_connectivity_configs,
    "get",
    return_value=DATABRICKS_NETWORK_CONNECTIVITY_CONFIGS,
)
def test_load_databricks_network_connectivity_configs(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)

    cartography.intel.databricks.network_connectivity_configs.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksNetworkConnectivityConfig",
        ["network_connectivity_config_id", "region"],
    ) == {("ncc-abc-123", "us-east-1")}

    # NCC -> Account RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksNetworkConnectivityConfig",
        "network_connectivity_config_id",
        "DatabricksAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("ncc-abc-123", DATABRICKS_ACCOUNT_ID)}
