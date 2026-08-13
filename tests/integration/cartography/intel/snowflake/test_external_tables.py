from unittest.mock import patch

import cartography.intel.snowflake.external_tables
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.external_tables import SNOWFLAKE_EXTERNAL_TABLES
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_file_formats import (
    _ensure_local_neo4j_has_test_file_formats,
)
from tests.integration.cartography.intel.snowflake.test_file_formats import LOG_CSV_ID
from tests.integration.cartography.intel.snowflake.test_schemas import (
    KWIK_E_MART_SCHEMA_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import (
    NUCLEAR_PLANT_SCHEMA_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import TEST_SCHEMAS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

PLANT_LOGS_ID = (
    "SPRINGFIELD.NUCLEAR/external_table/SPRINGFIELD.NUCLEAR_PLANT.PLANT_LOGS"
)
DONUT_SHIPMENTS_ID = (
    "SPRINGFIELD.NUCLEAR/external_table/SPRINGFIELD.KWIK_E_MART.DONUT_SHIPMENTS"
)
LOG_STAGE_ID = "SPRINGFIELD.NUCLEAR/stage/SPRINGFIELD.NUCLEAR_PLANT.LOG_STAGE"


def _ensure_local_neo4j_has_test_external_tables(neo4j_session) -> None:
    """Seed the Snowflake external tables for tests that need them in the graph."""
    _ensure_local_neo4j_has_test_file_formats(neo4j_session)
    with patch.object(
        cartography.intel.snowflake.external_tables,
        "get",
        return_value=(SNOWFLAKE_EXTERNAL_TABLES, True),
    ):
        cartography.intel.snowflake.external_tables.sync(
            neo4j_session,
            build_test_client(),
            TEST_SCHEMAS,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )


@patch.object(
    cartography.intel.snowflake.external_tables,
    "get",
    return_value=(SNOWFLAKE_EXTERNAL_TABLES, True),
)
def test_sync_snowflake_external_tables(mock_get, neo4j_session):
    # Arrange: the stage is owned by another sync, so seed the node the
    # file-access edge has to resolve against.
    _ensure_local_neo4j_has_test_file_formats(neo4j_session)
    neo4j_session.run(
        "MERGE (stage:SnowflakeStage {id: $stage_id})", stage_id=LOG_STAGE_ID
    )

    # Act
    complete = cartography.intel.snowflake.external_tables.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True

    # The rows never enter Snowflake storage, so the cloud location is the thing
    # that actually holds the data.
    assert check_nodes(
        neo4j_session,
        "SnowflakeExternalTable",
        ["id", "name", "qualified_name", "location", "invalid"],
    ) == {
        (
            PLANT_LOGS_ID,
            "PLANT_LOGS",
            "SPRINGFIELD.NUCLEAR_PLANT.PLANT_LOGS",
            "s3://springfield-plant-logs/control-room/",
            False,
        ),
        (
            DONUT_SHIPMENTS_ID,
            "DONUT_SHIPMENTS",
            "SPRINGFIELD.KWIK_E_MART.DONUT_SHIPMENTS",
            "s3://kwik-e-mart-shipments/",
            True,
        ),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeExternalTable",
        "id",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, PLANT_LOGS_ID),
        (SNOWFLAKE_ACCOUNT_ID, DONUT_SHIPMENTS_ID),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "id",
        "SnowflakeExternalTable",
        "id",
        "CONTAINS",
    ) == {
        (NUCLEAR_PLANT_SCHEMA_ID, PLANT_LOGS_ID),
        (KWIK_E_MART_SCHEMA_ID, DONUT_SHIPMENTS_ID),
    }

    # The `@`-prefixed stage reference resolves to the stage node.
    assert check_rels(
        neo4j_session,
        "SnowflakeExternalTable",
        "id",
        "SnowflakeStage",
        "id",
        "READS_FROM",
    ) == {(PLANT_LOGS_ID, LOG_STAGE_ID)}

    # Only the table naming a file format gets the parser edge; the other reports
    # a format type without a named format object.
    assert check_rels(
        neo4j_session,
        "SnowflakeExternalTable",
        "id",
        "SnowflakeFileFormat",
        "id",
        "USES_FILE_FORMAT",
    ) == {(PLANT_LOGS_ID, LOG_CSV_ID)}
