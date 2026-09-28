from unittest.mock import patch

import cartography.intel.snowflake.sequences
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.sequences import SNOWFLAKE_SEQUENCE_LISTINGS
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

EMPLOYEE_ID_SEQ_ID = (
    "SPRINGFIELD.NUCLEAR/sequence/SPRINGFIELD.NUCLEAR_PLANT.EMPLOYEE_ID_SEQ"
)


def _ensure_local_neo4j_has_test_sequences(neo4j_session) -> None:
    """Seed the Snowflake sequences for tests that need them in the graph."""
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    with patch.object(
        cartography.intel.snowflake.sequences,
        "get",
        return_value=(SNOWFLAKE_SEQUENCE_LISTINGS, True),
    ):
        cartography.intel.snowflake.sequences.sync(
            neo4j_session,
            build_test_client(),
            TEST_SCHEMAS,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )


@patch.object(
    cartography.intel.snowflake.sequences,
    "get",
    return_value=(SNOWFLAKE_SEQUENCE_LISTINGS, True),
)
def test_sync_snowflake_sequences(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_schemas(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.sequences.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True

    assert check_nodes(
        neo4j_session,
        "SnowflakeSequence",
        ["id", "name", "qualified_name", "start_value", "increment", "next_value"],
    ) == {
        (
            EMPLOYEE_ID_SEQ_ID,
            "EMPLOYEE_ID_SEQ",
            "SPRINGFIELD.NUCLEAR_PLANT.EMPLOYEE_ID_SEQ",
            1,
            1,
            743,
        ),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeSequence",
        "id",
        "RESOURCE",
    ) == {(SNOWFLAKE_ACCOUNT_ID, EMPLOYEE_ID_SEQ_ID)}

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "id",
        "SnowflakeSequence",
        "id",
        "CONTAINS",
    ) == {(NUCLEAR_PLANT_SCHEMA_ID, EMPLOYEE_ID_SEQ_ID)}
