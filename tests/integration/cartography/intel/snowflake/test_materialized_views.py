from unittest.mock import patch

import cartography.intel.snowflake.materialized_views
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.materialized_views import SNOWFLAKE_MATERIALIZED_VIEWS
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

DAILY_MELTDOWN_RISK_ID = (
    "SPRINGFIELD.NUCLEAR/materialized_view/"
    "SPRINGFIELD.NUCLEAR_PLANT.DAILY_MELTDOWN_RISK"
)
SQUISHEE_TOTALS_ID = (
    "SPRINGFIELD.NUCLEAR/materialized_view/SPRINGFIELD.KWIK_E_MART.SQUISHEE_TOTALS"
)


def _ensure_local_neo4j_has_test_materialized_views(neo4j_session) -> None:
    """Seed the Snowflake materialized views for tests that need them in the graph."""
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    with patch.object(
        cartography.intel.snowflake.materialized_views,
        "get",
        return_value=(SNOWFLAKE_MATERIALIZED_VIEWS, True),
    ):
        cartography.intel.snowflake.materialized_views.sync(
            neo4j_session,
            build_test_client(),
            TEST_SCHEMAS,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )


@patch.object(
    cartography.intel.snowflake.materialized_views,
    "get",
    return_value=(SNOWFLAKE_MATERIALIZED_VIEWS, True),
)
def test_sync_snowflake_materialized_views(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_schemas(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.materialized_views.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True

    # The SQL API hands back every cell as a string, so the booleans and counts
    # below prove the coercion happened.
    assert check_nodes(
        neo4j_session,
        "SnowflakeMaterializedView",
        [
            "id",
            "name",
            "qualified_name",
            "is_secure",
            "invalid",
            "automatic_clustering",
            "row_count",
            "size_bytes",
        ],
    ) == {
        (
            DAILY_MELTDOWN_RISK_ID,
            "DAILY_MELTDOWN_RISK",
            "SPRINGFIELD.NUCLEAR_PLANT.DAILY_MELTDOWN_RISK",
            False,
            False,
            True,
            365,
            24576,
        ),
        (
            SQUISHEE_TOTALS_ID,
            "SQUISHEE_TOTALS",
            "SPRINGFIELD.KWIK_E_MART.SQUISHEE_TOTALS",
            True,
            True,
            False,
            12,
            4096,
        ),
    }

    # An invalidated materialized view records why, and a healthy one keeps null.
    assert check_nodes(
        neo4j_session, "SnowflakeMaterializedView", ["name", "invalid_reason"]
    ) == {
        ("DAILY_MELTDOWN_RISK", None),
        ("SQUISHEE_TOTALS", "Base table altered"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeMaterializedView",
        "id",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, DAILY_MELTDOWN_RISK_ID),
        (SNOWFLAKE_ACCOUNT_ID, SQUISHEE_TOTALS_ID),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "id",
        "SnowflakeMaterializedView",
        "id",
        "CONTAINS",
    ) == {
        (NUCLEAR_PLANT_SCHEMA_ID, DAILY_MELTDOWN_RISK_ID),
        (KWIK_E_MART_SCHEMA_ID, SQUISHEE_TOTALS_ID),
    }
