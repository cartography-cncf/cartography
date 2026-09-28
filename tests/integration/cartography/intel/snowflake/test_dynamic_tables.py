from unittest.mock import patch

import cartography.intel.snowflake.dynamic_tables
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.dynamic_tables import SNOWFLAKE_DYNAMIC_TABLE_LISTINGS
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_schemas import (
    _ensure_local_neo4j_has_test_schemas,
)
from tests.integration.cartography.intel.snowflake.test_schemas import (
    NUCLEAR_PLANT_SCHEMA_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import TEST_SCHEMAS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

COOLANT_TRENDS_ID = (
    "SPRINGFIELD.NUCLEAR/dynamic_table/SPRINGFIELD.NUCLEAR_PLANT.COOLANT_TRENDS"
)
MELTDOWN_ALERTS_ID = (
    "SPRINGFIELD.NUCLEAR/dynamic_table/SPRINGFIELD.NUCLEAR_PLANT.MELTDOWN_ALERTS"
)
DUFF_WAREHOUSE_ID = "SPRINGFIELD.NUCLEAR/warehouse/DUFF_WH"


def _ensure_local_neo4j_has_test_dynamic_tables(neo4j_session) -> None:
    """Seed the Snowflake dynamic tables for tests that need them in the graph."""
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    with patch.object(
        cartography.intel.snowflake.dynamic_tables,
        "get",
        return_value=(SNOWFLAKE_DYNAMIC_TABLE_LISTINGS, True),
    ):
        cartography.intel.snowflake.dynamic_tables.sync(
            neo4j_session,
            build_test_client(),
            TEST_SCHEMAS,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )


@patch.object(
    cartography.intel.snowflake.dynamic_tables,
    "get",
    return_value=(SNOWFLAKE_DYNAMIC_TABLE_LISTINGS, True),
)
def test_sync_snowflake_dynamic_tables(mock_get, neo4j_session):
    # Arrange: the warehouse is owned by another sync, so seed the node the
    # refresh-compute edge has to resolve against.
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    neo4j_session.run(
        "MERGE (warehouse:SnowflakeWarehouse {id: $warehouse_id})",
        warehouse_id=DUFF_WAREHOUSE_ID,
    )

    # Act
    complete = cartography.intel.snowflake.dynamic_tables.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True

    # A SUSPENDED dynamic table keeps serving stale rows without failing queries.
    assert check_nodes(
        neo4j_session,
        "SnowflakeDynamicTable",
        ["id", "name", "qualified_name", "refresh_mode", "scheduling_state"],
    ) == {
        (
            COOLANT_TRENDS_ID,
            "COOLANT_TRENDS",
            "SPRINGFIELD.NUCLEAR_PLANT.COOLANT_TRENDS",
            "INCREMENTAL",
            "RUNNING",
        ),
        (
            MELTDOWN_ALERTS_ID,
            "MELTDOWN_ALERTS",
            "SPRINGFIELD.NUCLEAR_PLANT.MELTDOWN_ALERTS",
            "FULL",
            "SUSPENDED",
        ),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeDynamicTable",
        "id",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, COOLANT_TRENDS_ID),
        (SNOWFLAKE_ACCOUNT_ID, MELTDOWN_ALERTS_ID),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "id",
        "SnowflakeDynamicTable",
        "id",
        "CONTAINS",
    ) == {
        (NUCLEAR_PLANT_SCHEMA_ID, COOLANT_TRENDS_ID),
        (NUCLEAR_PLANT_SCHEMA_ID, MELTDOWN_ALERTS_ID),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeDynamicTable",
        "id",
        "SnowflakeWarehouse",
        "id",
        "USES_WAREHOUSE",
    ) == {
        (COOLANT_TRENDS_ID, DUFF_WAREHOUSE_ID),
        (MELTDOWN_ALERTS_ID, DUFF_WAREHOUSE_ID),
    }
