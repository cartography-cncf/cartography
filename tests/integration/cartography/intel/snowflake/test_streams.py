from unittest.mock import patch

import cartography.intel.snowflake.streams
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.streams import SNOWFLAKE_STREAM_LISTINGS
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_schemas import (
    NUCLEAR_PLANT_SCHEMA_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import TEST_SCHEMAS
from tests.integration.cartography.intel.snowflake.test_tables import (
    _ensure_local_neo4j_has_test_tables,
)
from tests.integration.cartography.intel.snowflake.test_tables import (
    REACTOR_READINGS_TABLE_ID,
)
from tests.integration.cartography.intel.snowflake.test_tables import (
    SQUISHEE_SALES_TABLE_ID,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

REACTOR_READINGS_STREAM_ID = (
    "SPRINGFIELD.NUCLEAR/stream/SPRINGFIELD.NUCLEAR_PLANT.REACTOR_READINGS_STREAM"
)
SQUISHEE_SALES_STREAM_ID = (
    "SPRINGFIELD.NUCLEAR/stream/SPRINGFIELD.NUCLEAR_PLANT.SQUISHEE_SALES_STREAM"
)
LOG_STAGE_STREAM_ID = (
    "SPRINGFIELD.NUCLEAR/stream/SPRINGFIELD.NUCLEAR_PLANT.LOG_STAGE_STREAM"
)


def _ensure_local_neo4j_has_test_streams(neo4j_session) -> None:
    """Seed the Snowflake streams for tests that need them in the graph."""
    _ensure_local_neo4j_has_test_tables(neo4j_session)
    with patch.object(
        cartography.intel.snowflake.streams,
        "get",
        return_value=(SNOWFLAKE_STREAM_LISTINGS, True),
    ):
        cartography.intel.snowflake.streams.sync(
            neo4j_session,
            build_test_client(),
            TEST_SCHEMAS,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )


@patch.object(
    cartography.intel.snowflake.streams,
    "get",
    return_value=(SNOWFLAKE_STREAM_LISTINGS, True),
)
def test_sync_snowflake_streams(mock_get, neo4j_session):
    # Arrange: the source tables have to exist for the change-feed edge to resolve.
    _ensure_local_neo4j_has_test_tables(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.streams.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True

    # A stale stream has quietly stopped delivering changes.
    assert check_nodes(
        neo4j_session,
        "SnowflakeStream",
        ["id", "name", "source_type", "source_name", "mode", "is_stale"],
    ) == {
        (
            REACTOR_READINGS_STREAM_ID,
            "REACTOR_READINGS_STREAM",
            "Table",
            "SPRINGFIELD.NUCLEAR_PLANT.REACTOR_READINGS",
            "DEFAULT",
            False,
        ),
        (
            SQUISHEE_SALES_STREAM_ID,
            "SQUISHEE_SALES_STREAM",
            "Table",
            "SPRINGFIELD.KWIK_E_MART.SQUISHEE_SALES",
            "APPEND_ONLY",
            True,
        ),
        (
            LOG_STAGE_STREAM_ID,
            "LOG_STAGE_STREAM",
            "Stage",
            None,
            "DEFAULT",
            False,
        ),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeStream",
        "id",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, REACTOR_READINGS_STREAM_ID),
        (SNOWFLAKE_ACCOUNT_ID, SQUISHEE_SALES_STREAM_ID),
        (SNOWFLAKE_ACCOUNT_ID, LOG_STAGE_STREAM_ID),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "id",
        "SnowflakeStream",
        "id",
        "CONTAINS",
    ) == {
        (NUCLEAR_PLANT_SCHEMA_ID, REACTOR_READINGS_STREAM_ID),
        (NUCLEAR_PLANT_SCHEMA_ID, SQUISHEE_SALES_STREAM_ID),
        (NUCLEAR_PLANT_SCHEMA_ID, LOG_STAGE_STREAM_ID),
    }

    # A stream reaches across schemas to its source, and the stage-sourced stream
    # gets no table edge at all.
    assert check_rels(
        neo4j_session,
        "SnowflakeStream",
        "id",
        "SnowflakeTable",
        "id",
        "READS_FROM",
    ) == {
        (REACTOR_READINGS_STREAM_ID, REACTOR_READINGS_TABLE_ID),
        (SQUISHEE_SALES_STREAM_ID, SQUISHEE_SALES_TABLE_ID),
    }
