from unittest.mock import patch

import cartography.intel.snowflake.iceberg_tables
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.iceberg_tables import SNOWFLAKE_ICEBERG_TABLE_LISTINGS
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_schemas import (
    _ensure_local_neo4j_has_test_schemas,
)
from tests.integration.cartography.intel.snowflake.test_schemas import (
    MONORAIL_VOLUME_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import (
    NUCLEAR_PLANT_SCHEMA_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import TEST_SCHEMAS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

RADIATION_SAMPLES_ID = (
    "SPRINGFIELD.NUCLEAR/iceberg_table/SPRINGFIELD.NUCLEAR_PLANT.RADIATION_SAMPLES"
)
INSPECTION_ARCHIVE_ID = (
    "SPRINGFIELD.NUCLEAR/iceberg_table/SPRINGFIELD.NUCLEAR_PLANT.INSPECTION_ARCHIVE"
)
GLUE_CATALOG_ID = "SPRINGFIELD.NUCLEAR/catalog_integration/GLUE_CATALOG"


def _ensure_local_neo4j_has_test_iceberg_tables(neo4j_session) -> None:
    """Seed the Snowflake Iceberg tables for tests that need them in the graph."""
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    with patch.object(
        cartography.intel.snowflake.iceberg_tables,
        "get",
        return_value=(SNOWFLAKE_ICEBERG_TABLE_LISTINGS, True),
    ):
        cartography.intel.snowflake.iceberg_tables.sync(
            neo4j_session,
            build_test_client(),
            TEST_SCHEMAS,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )


@patch.object(
    cartography.intel.snowflake.iceberg_tables,
    "get",
    return_value=(SNOWFLAKE_ICEBERG_TABLE_LISTINGS, True),
)
def test_sync_snowflake_iceberg_tables(mock_get, neo4j_session):
    # Arrange: the external volume and the catalog integration are owned by other
    # syncs, so seed the nodes those edges have to resolve against.
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    neo4j_session.run(
        "MERGE (volume:SnowflakeExternalVolume {id: $volume_id})",
        volume_id=MONORAIL_VOLUME_ID,
    )
    neo4j_session.run(
        "MERGE (catalog:SnowflakeCatalogIntegration {id: $catalog_id})",
        catalog_id=GLUE_CATALOG_ID,
    )

    # Act
    complete = cartography.intel.snowflake.iceberg_tables.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True

    assert check_nodes(
        neo4j_session,
        "SnowflakeIcebergTable",
        [
            "id",
            "name",
            "qualified_name",
            "catalog",
            "iceberg_table_type",
            "can_write_metadata",
        ],
    ) == {
        (
            RADIATION_SAMPLES_ID,
            "RADIATION_SAMPLES",
            "SPRINGFIELD.NUCLEAR_PLANT.RADIATION_SAMPLES",
            "SNOWFLAKE",
            "MANAGED",
            True,
        ),
        (
            INSPECTION_ARCHIVE_ID,
            "INSPECTION_ARCHIVE",
            "SPRINGFIELD.NUCLEAR_PLANT.INSPECTION_ARCHIVE",
            "GLUE_CATALOG",
            "UNMANAGED",
            False,
        ),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeIcebergTable",
        "id",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, RADIATION_SAMPLES_ID),
        (SNOWFLAKE_ACCOUNT_ID, INSPECTION_ARCHIVE_ID),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "id",
        "SnowflakeIcebergTable",
        "id",
        "CONTAINS",
    ) == {
        (NUCLEAR_PLANT_SCHEMA_ID, RADIATION_SAMPLES_ID),
        (NUCLEAR_PLANT_SCHEMA_ID, INSPECTION_ARCHIVE_ID),
    }

    # Both tables' files sit on customer-owned storage.
    assert check_rels(
        neo4j_session,
        "SnowflakeIcebergTable",
        "id",
        "SnowflakeExternalVolume",
        "id",
        "STORED_IN",
    ) == {
        (RADIATION_SAMPLES_ID, MONORAIL_VOLUME_ID),
        (INSPECTION_ARCHIVE_ID, MONORAIL_VOLUME_ID),
    }

    # Only the externally catalogued table gets a catalog edge: the literal
    # SNOWFLAKE catalog is Snowflake itself, not an integration object.
    assert check_rels(
        neo4j_session,
        "SnowflakeIcebergTable",
        "id",
        "SnowflakeCatalogIntegration",
        "id",
        "USES_CATALOG",
    ) == {(INSPECTION_ARCHIVE_ID, GLUE_CATALOG_ID)}
