from unittest.mock import patch

import cartography.intel.snowflake.warehouses
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.warehouses import SNOWFLAKE_WAREHOUSES
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_resource_monitors import (
    _ensure_local_neo4j_has_test_resource_monitors,
)
from tests.integration.cartography.intel.snowflake.test_resource_monitors import (
    PLANT_BUDGET_MONITOR_ID,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

REACTOR_WH_ID = "SPRINGFIELD.NUCLEAR/warehouse/REACTOR_WH"
DONUT_WH_ID = "SPRINGFIELD.NUCLEAR/warehouse/DONUT_WH"


def _ensure_local_neo4j_has_test_warehouses(neo4j_session) -> None:
    """Seed the warehouses a service's USES_WAREHOUSE edge resolves against."""
    _ensure_local_neo4j_has_test_account(neo4j_session)
    cartography.intel.snowflake.warehouses.load_warehouses(
        neo4j_session,
        cartography.intel.snowflake.warehouses.transform(
            SNOWFLAKE_WAREHOUSES, SNOWFLAKE_ACCOUNT_ID
        ),
        SNOWFLAKE_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.snowflake.warehouses,
    "get",
    return_value=SNOWFLAKE_WAREHOUSES,
)
def test_sync_snowflake_warehouses(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_resource_monitors(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.warehouses.sync(
        neo4j_session,
        build_test_client(),
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the size is read whichever field name the API version used, and a
    # warehouse with no auto-suspend reports null, which is what makes "bills until
    # someone notices" visible.
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeWarehouse",
        ["id", "name", "size", "state", "auto_suspend", "resource_monitor"],
    ) == {
        (
            REACTOR_WH_ID,
            "REACTOR_WH",
            "X-Large",
            "STARTED",
            600,
            "PLANT_BUDGET_MONITOR",
        ),
        (DONUT_WH_ID, "DONUT_WH", "Medium", "SUSPENDED", None, None),
    }
    # Every warehouse carries the ComputeCluster ontology label.
    assert check_nodes(neo4j_session, "ComputeCluster", ["id"]) >= {
        (REACTOR_WH_ID,),
        (DONUT_WH_ID,),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeWarehouse",
        "id",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (REACTOR_WH_ID, SNOWFLAKE_ACCOUNT_ID),
        (DONUT_WH_ID, SNOWFLAKE_ACCOUNT_ID),
    }
    # Only the monitored warehouse gets the edge: DONUT_WH names no monitor, so no
    # edge is invented for it.
    assert check_rels(
        neo4j_session,
        "SnowflakeWarehouse",
        "id",
        "SnowflakeResourceMonitor",
        "id",
        "MONITORED_BY",
        rel_direction_right=True,
    ) == {(REACTOR_WH_ID, PLANT_BUDGET_MONITOR_ID)}
