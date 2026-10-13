from unittest.mock import patch

import cartography.intel.snowflake.file_formats
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.file_formats import SNOWFLAKE_FILE_FORMATS
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

LOG_CSV_ID = "SPRINGFIELD.NUCLEAR/file_format/SPRINGFIELD.NUCLEAR_PLANT.LOG_CSV"
SHIPMENT_JSON_ID = (
    "SPRINGFIELD.NUCLEAR/file_format/SPRINGFIELD.KWIK_E_MART.SHIPMENT_JSON"
)


def _ensure_local_neo4j_has_test_file_formats(neo4j_session) -> None:
    """Seed the file formats the external-table sync resolves its parser against."""
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    with patch.object(
        cartography.intel.snowflake.file_formats,
        "get",
        return_value=(SNOWFLAKE_FILE_FORMATS, True),
    ):
        cartography.intel.snowflake.file_formats.sync(
            neo4j_session,
            build_test_client(),
            TEST_SCHEMAS,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )


@patch.object(
    cartography.intel.snowflake.file_formats,
    "get",
    return_value=(SNOWFLAKE_FILE_FORMATS, True),
)
def test_sync_snowflake_file_formats(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_schemas(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.file_formats.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True

    assert check_nodes(
        neo4j_session,
        "SnowflakeFileFormat",
        ["id", "name", "qualified_name", "format_type"],
    ) == {
        (LOG_CSV_ID, "LOG_CSV", "SPRINGFIELD.NUCLEAR_PLANT.LOG_CSV", "CSV"),
        (
            SHIPMENT_JSON_ID,
            "SHIPMENT_JSON",
            "SPRINGFIELD.KWIK_E_MART.SHIPMENT_JSON",
            "JSON",
        ),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeFileFormat",
        "id",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, LOG_CSV_ID),
        (SNOWFLAKE_ACCOUNT_ID, SHIPMENT_JSON_ID),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "id",
        "SnowflakeFileFormat",
        "id",
        "CONTAINS",
    ) == {
        (NUCLEAR_PLANT_SCHEMA_ID, LOG_CSV_ID),
        (KWIK_E_MART_SCHEMA_ID, SHIPMENT_JSON_ID),
    }
