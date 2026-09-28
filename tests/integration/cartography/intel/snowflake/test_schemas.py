from unittest.mock import patch

import cartography.intel.snowflake.schemas
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.schemas import SNOWFLAKE_SCHEMAS
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_databases import (
    _ensure_local_neo4j_has_test_databases,
)
from tests.integration.cartography.intel.snowflake.test_databases import (
    MONORAIL_DATABASE_ID,
)
from tests.integration.cartography.intel.snowflake.test_databases import (
    SPRINGFIELD_DATABASE_ID,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

NUCLEAR_PLANT_SCHEMA_ID = "SPRINGFIELD.NUCLEAR/schema/SPRINGFIELD.NUCLEAR_PLANT"
KWIK_E_MART_SCHEMA_ID = "SPRINGFIELD.NUCLEAR/schema/SPRINGFIELD.KWIK_E_MART"
MONORAIL_PUBLIC_SCHEMA_ID = "SPRINGFIELD.NUCLEAR/schema/MONORAIL.PUBLIC"

MONORAIL_VOLUME_ID = "SPRINGFIELD.NUCLEAR/external_volume/MONORAIL_VOLUME"

# The parent list every object-level sync walks: only the database and schema name
# are read off it.
TEST_SCHEMAS = [
    {"database_name": schema["database_name"], "name": schema["name"]}
    for schema in SNOWFLAKE_SCHEMAS
]


def _ensure_local_neo4j_has_test_schemas(neo4j_session) -> None:
    """Seed the Snowflake schemas every object-level sync hangs its CONTAINS edge off."""
    _ensure_local_neo4j_has_test_databases(neo4j_session)
    with patch.object(
        cartography.intel.snowflake.schemas,
        "get",
        return_value=(SNOWFLAKE_SCHEMAS, True),
    ):
        cartography.intel.snowflake.schemas.sync(
            neo4j_session,
            build_test_client(),
            [{"name": "SPRINGFIELD"}, {"name": "MONORAIL"}],
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )


@patch.object(
    cartography.intel.snowflake.schemas,
    "get",
    return_value=(SNOWFLAKE_SCHEMAS, True),
)
def test_sync_snowflake_schemas(mock_get, neo4j_session):
    # Arrange: the external volume is owned by another sync, so seed the node the
    # default-volume edge has to resolve against.
    _ensure_local_neo4j_has_test_databases(neo4j_session)
    neo4j_session.run(
        "MERGE (volume:SnowflakeExternalVolume {id: $volume_id})",
        volume_id=MONORAIL_VOLUME_ID,
    )

    # Act
    schemas, complete = cartography.intel.snowflake.schemas.sync(
        neo4j_session,
        build_test_client(),
        [{"name": "SPRINGFIELD"}, {"name": "MONORAIL"}],
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True
    assert len(schemas) == 3

    assert check_nodes(
        neo4j_session,
        "SnowflakeSchema",
        ["id", "name", "qualified_name", "database_name", "managed_access"],
    ) == {
        (
            NUCLEAR_PLANT_SCHEMA_ID,
            "NUCLEAR_PLANT",
            "SPRINGFIELD.NUCLEAR_PLANT",
            "SPRINGFIELD",
            True,
        ),
        (
            KWIK_E_MART_SCHEMA_ID,
            "KWIK_E_MART",
            "SPRINGFIELD.KWIK_E_MART",
            "SPRINGFIELD",
            False,
        ),
        (
            MONORAIL_PUBLIC_SCHEMA_ID,
            "PUBLIC",
            "MONORAIL.PUBLIC",
            "MONORAIL",
            False,
        ),
    }

    # Assert the sub-resource edge points at the account rather than the database.
    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeSchema",
        "id",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, NUCLEAR_PLANT_SCHEMA_ID),
        (SNOWFLAKE_ACCOUNT_ID, KWIK_E_MART_SCHEMA_ID),
        (SNOWFLAKE_ACCOUNT_ID, MONORAIL_PUBLIC_SCHEMA_ID),
    }

    # Assert containment is a separate edge from the database.
    assert check_rels(
        neo4j_session,
        "SnowflakeDatabase",
        "id",
        "SnowflakeSchema",
        "id",
        "CONTAINS",
    ) == {
        (SPRINGFIELD_DATABASE_ID, NUCLEAR_PLANT_SCHEMA_ID),
        (SPRINGFIELD_DATABASE_ID, KWIK_E_MART_SCHEMA_ID),
        (MONORAIL_DATABASE_ID, MONORAIL_PUBLIC_SCHEMA_ID),
    }

    # Only the schema that names a default volume gets the storage edge.
    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "id",
        "SnowflakeExternalVolume",
        "id",
        "DEFAULT_EXTERNAL_VOLUME",
    ) == {(NUCLEAR_PLANT_SCHEMA_ID, MONORAIL_VOLUME_ID)}
