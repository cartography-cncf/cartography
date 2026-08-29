from unittest.mock import patch

import cartography.intel.snowflake.tables
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.tables import SNOWFLAKE_TABLES
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_schemas import (
    _ensure_local_neo4j_has_test_schemas,
)
from tests.integration.cartography.intel.snowflake.test_schemas import (
    KWIK_E_MART_SCHEMA_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import (
    NUCLEAR_PLANT_SCHEMA_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import TEST_SCHEMAS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

REACTOR_READINGS_TABLE_ID = (
    "SPRINGFIELD.NUCLEAR/table/SPRINGFIELD.NUCLEAR_PLANT.REACTOR_READINGS"
)
SQUISHEE_SALES_TABLE_ID = (
    "SPRINGFIELD.NUCLEAR/table/SPRINGFIELD.KWIK_E_MART.SQUISHEE_SALES"
)


def _ensure_local_neo4j_has_test_tables(neo4j_session) -> None:
    """Seed the Snowflake tables the stream sync resolves its source against."""
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    with patch.object(
        cartography.intel.snowflake.tables,
        "get",
        return_value=(SNOWFLAKE_TABLES, True),
    ):
        cartography.intel.snowflake.tables.sync(
            neo4j_session,
            build_test_client(),
            TEST_SCHEMAS,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )


@patch.object(
    cartography.intel.snowflake.tables,
    "get",
    return_value=(SNOWFLAKE_TABLES, True),
)
def test_sync_snowflake_tables(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_schemas(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.tables.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True

    # The column payload is collapsed into a count rather than becoming nodes.
    assert check_nodes(
        neo4j_session,
        "SnowflakeTable",
        [
            "id",
            "name",
            "qualified_name",
            "table_type",
            "row_count",
            "size_bytes",
            "column_count",
            "change_tracking",
            "enable_schema_evolution",
        ],
    ) == {
        (
            REACTOR_READINGS_TABLE_ID,
            "REACTOR_READINGS",
            "SPRINGFIELD.NUCLEAR_PLANT.REACTOR_READINGS",
            "NORMAL",
            480000,
            12582912,
            3,
            True,
            False,
        ),
        (
            SQUISHEE_SALES_TABLE_ID,
            "SQUISHEE_SALES",
            "SPRINGFIELD.KWIK_E_MART.SQUISHEE_SALES",
            "NORMAL",
            1200,
            40960,
            2,
            False,
            True,
        ),
    }

    # An empty clustering key is stored as null, never as an empty string.
    assert check_nodes(neo4j_session, "SnowflakeTable", ["name", "cluster_by"]) == {
        ("REACTOR_READINGS", "LINEAR(RECORDED_AT)"),
        ("SQUISHEE_SALES", None),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeTable",
        "id",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, REACTOR_READINGS_TABLE_ID),
        (SNOWFLAKE_ACCOUNT_ID, SQUISHEE_SALES_TABLE_ID),
    }

    # The recomputed parent id matches the schema node's own id byte for byte.
    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "id",
        "SnowflakeTable",
        "id",
        "CONTAINS",
    ) == {
        (NUCLEAR_PLANT_SCHEMA_ID, REACTOR_READINGS_TABLE_ID),
        (KWIK_E_MART_SCHEMA_ID, SQUISHEE_SALES_TABLE_ID),
    }


@patch.object(
    cartography.intel.snowflake.tables,
    "get",
    return_value=(SNOWFLAKE_TABLES, False),
)
def test_sync_snowflake_tables_reports_an_unreadable_schema(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_schemas(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.tables.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the caller is told the walk was partial so it can skip cleanup and
    # keep tables it merely failed to re-read.
    assert complete is False
