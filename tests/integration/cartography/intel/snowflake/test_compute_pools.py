from unittest.mock import patch

import cartography.intel.snowflake.compute_pools
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.compute_pools import SNOWFLAKE_COMPUTE_POOLS
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

MONORAIL_POOL_ID = "SPRINGFIELD.NUCLEAR/compute_pool/MONORAIL_POOL"
KWIK_E_MART_POOL_ID = "SPRINGFIELD.NUCLEAR/compute_pool/KWIK_E_MART_POOL"


def _ensure_local_neo4j_has_test_compute_pools(neo4j_session) -> None:
    """Seed the compute pools a service's WORKLOAD_PARENT edge resolves against."""
    _ensure_local_neo4j_has_test_account(neo4j_session)
    cartography.intel.snowflake.compute_pools.load_compute_pools(
        neo4j_session,
        cartography.intel.snowflake.compute_pools.transform(
            SNOWFLAKE_COMPUTE_POOLS, SNOWFLAKE_ACCOUNT_ID
        ),
        SNOWFLAKE_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.snowflake.compute_pools,
    "get",
    return_value=SNOWFLAKE_COMPUTE_POOLS,
)
def test_sync_snowflake_compute_pools(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_account(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.compute_pools.sync(
        neo4j_session,
        build_test_client(),
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: a pool dedicated to a Native App is distinguishable from a shared one,
    # because only the shared pools can host the account's own services.
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeComputePool",
        ["id", "name", "state", "instance_family", "is_exclusive", "application"],
    ) == {
        (MONORAIL_POOL_ID, "MONORAIL_POOL", "ACTIVE", "CPU_X64_S", False, None),
        (
            KWIK_E_MART_POOL_ID,
            "KWIK_E_MART_POOL",
            "SUSPENDED",
            "GPU_NV_S",
            True,
            "SQUISHEE_FORECASTER",
        ),
    }
    assert check_nodes(neo4j_session, "ComputeCluster", ["id"]) >= {
        (MONORAIL_POOL_ID,),
        (KWIK_E_MART_POOL_ID,),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeComputePool",
        "id",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (MONORAIL_POOL_ID, SNOWFLAKE_ACCOUNT_ID),
        (KWIK_E_MART_POOL_ID, SNOWFLAKE_ACCOUNT_ID),
    }
