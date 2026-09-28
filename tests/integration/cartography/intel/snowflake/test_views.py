from unittest.mock import patch

import cartography.intel.snowflake.views
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.views import SNOWFLAKE_VIEWS
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

SAFETY_INSPECTIONS_VIEW_ID = (
    "SPRINGFIELD.NUCLEAR/view/SPRINGFIELD.NUCLEAR_PLANT.SAFETY_INSPECTIONS"
)
DONUT_INVENTORY_VIEW_ID = (
    "SPRINGFIELD.NUCLEAR/view/SPRINGFIELD.KWIK_E_MART.DONUT_INVENTORY"
)


def _ensure_local_neo4j_has_test_views(neo4j_session) -> None:
    """Seed the Snowflake views for tests that need them already in the graph."""
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    with patch.object(
        cartography.intel.snowflake.views,
        "get",
        return_value=(SNOWFLAKE_VIEWS, True),
    ):
        cartography.intel.snowflake.views.sync(
            neo4j_session,
            build_test_client(),
            TEST_SCHEMAS,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )


@patch.object(
    cartography.intel.snowflake.views,
    "get",
    return_value=(SNOWFLAKE_VIEWS, True),
)
def test_sync_snowflake_views(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_schemas(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.views.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True

    # `is_secure` is the security-relevant field: a non-secure view can leak both
    # its definition and the rows it was written to filter out.
    assert check_nodes(
        neo4j_session,
        "SnowflakeView",
        ["id", "name", "qualified_name", "is_secure", "column_count"],
    ) == {
        (
            SAFETY_INSPECTIONS_VIEW_ID,
            "SAFETY_INSPECTIONS",
            "SPRINGFIELD.NUCLEAR_PLANT.SAFETY_INSPECTIONS",
            True,
            2,
        ),
        (
            DONUT_INVENTORY_VIEW_ID,
            "DONUT_INVENTORY",
            "SPRINGFIELD.KWIK_E_MART.DONUT_INVENTORY",
            False,
            2,
        ),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeView",
        "id",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, SAFETY_INSPECTIONS_VIEW_ID),
        (SNOWFLAKE_ACCOUNT_ID, DONUT_INVENTORY_VIEW_ID),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "id",
        "SnowflakeView",
        "id",
        "CONTAINS",
    ) == {
        (NUCLEAR_PLANT_SCHEMA_ID, SAFETY_INSPECTIONS_VIEW_ID),
        (KWIK_E_MART_SCHEMA_ID, DONUT_INVENTORY_VIEW_ID),
    }
