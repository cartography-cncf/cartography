from unittest.mock import patch

import cartography.intel.snowflake.alerts
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.alerts import SNOWFLAKE_ALERTS
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_tasks import (
    seed_schema_level_dependencies,
)
from tests.integration.cartography.intel.snowflake.test_tasks import TEST_SCHEMA_NAME
from tests.integration.cartography.intel.snowflake.test_tasks import TEST_SCHEMAS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


@patch.object(cartography.intel.snowflake.alerts, "get", return_value=SNOWFLAKE_ALERTS)
def test_sync_snowflake_alerts(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    seed_schema_level_dependencies(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.alerts.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert
    assert complete is True
    assert check_nodes(neo4j_session, "SnowflakeAlert", ["name", "state"]) == {
        ("MELTDOWN_WATCH", "started"),
        ("DONUT_SHORTAGE", "suspended"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeAlert",
        "name",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, "MELTDOWN_WATCH"),
        (SNOWFLAKE_ACCOUNT_ID, "DONUT_SHORTAGE"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "name",
        "SnowflakeAlert",
        "name",
        "CONTAINS",
    ) == {
        (TEST_SCHEMA_NAME, "MELTDOWN_WATCH"),
        (TEST_SCHEMA_NAME, "DONUT_SHORTAGE"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAlert",
        "name",
        "SnowflakeWarehouse",
        "name",
        "USES_WAREHOUSE",
    ) == {("MELTDOWN_WATCH", "SECTOR_7G_WH")}
