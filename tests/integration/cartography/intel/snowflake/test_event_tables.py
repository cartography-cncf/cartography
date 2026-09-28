from unittest.mock import patch

import cartography.intel.snowflake.event_tables
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.event_tables import SNOWFLAKE_EVENT_TABLE_LISTINGS
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

PLANT_EVENTS_ID = (
    "SPRINGFIELD.NUCLEAR/event_table/SPRINGFIELD.NUCLEAR_PLANT.PLANT_EVENTS"
)


def _ensure_local_neo4j_has_test_event_tables(neo4j_session) -> None:
    """Seed the Snowflake event tables for tests that need them in the graph."""
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    with patch.object(
        cartography.intel.snowflake.event_tables,
        "get",
        return_value=(SNOWFLAKE_EVENT_TABLE_LISTINGS, True),
    ):
        cartography.intel.snowflake.event_tables.sync(
            neo4j_session,
            build_test_client(),
            TEST_SCHEMAS,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )


@patch.object(
    cartography.intel.snowflake.event_tables,
    "get",
    return_value=(SNOWFLAKE_EVENT_TABLE_LISTINGS, True),
)
def test_sync_snowflake_event_tables(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_schemas(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.event_tables.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True

    assert check_nodes(
        neo4j_session,
        "SnowflakeEventTable",
        ["id", "name", "qualified_name", "row_count", "size_bytes"],
    ) == {
        (
            PLANT_EVENTS_ID,
            "PLANT_EVENTS",
            "SPRINGFIELD.NUCLEAR_PLANT.PLANT_EVENTS",
            9100000,
            734003200,
        ),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeEventTable",
        "id",
        "RESOURCE",
    ) == {(SNOWFLAKE_ACCOUNT_ID, PLANT_EVENTS_ID)}

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "id",
        "SnowflakeEventTable",
        "id",
        "CONTAINS",
    ) == {(NUCLEAR_PLANT_SCHEMA_ID, PLANT_EVENTS_ID)}
