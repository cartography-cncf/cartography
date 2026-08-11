from unittest.mock import patch

import cartography.intel.snowflake.resource_monitors
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.resource_monitors import SNOWFLAKE_RESOURCE_MONITORS
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

PLANT_BUDGET_MONITOR_ID = "SPRINGFIELD.NUCLEAR/resource_monitor/PLANT_BUDGET_MONITOR"
DUFF_MONITOR_ID = "SPRINGFIELD.NUCLEAR/resource_monitor/DUFF_MONITOR"


def _ensure_local_neo4j_has_test_resource_monitors(neo4j_session) -> None:
    """Seed the resource monitors a warehouse's MONITORED_BY edge resolves against."""
    _ensure_local_neo4j_has_test_account(neo4j_session)
    cartography.intel.snowflake.resource_monitors.load_resource_monitors(
        neo4j_session,
        cartography.intel.snowflake.resource_monitors.transform(
            SNOWFLAKE_RESOURCE_MONITORS, SNOWFLAKE_ACCOUNT_ID
        ),
        SNOWFLAKE_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.snowflake.resource_monitors,
    "get",
    return_value=SNOWFLAKE_RESOURCE_MONITORS,
)
def test_sync_snowflake_resource_monitors(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_account(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.resource_monitors.sync(
        neo4j_session,
        build_test_client(),
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the SQL API's percentage strings become integers, and a monitor with no
    # suspend threshold reports null rather than zero, because "never suspends" and
    # "suspends at 0%" are opposite facts.
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeResourceMonitor",
        ["id", "name", "credit_quota", "used_credits", "level", "suspend_at"],
    ) == {
        (
            PLANT_BUDGET_MONITOR_ID,
            "PLANT_BUDGET_MONITOR",
            5000.0,
            1234.5,
            "WAREHOUSE",
            100,
        ),
        (DUFF_MONITOR_ID, "DUFF_MONITOR", 100.0, 99.0, "ACCOUNT", None),
    }
    # check_nodes cannot carry a list property through a set of tuples, so the
    # threshold list is read directly.
    assert {
        (row["id"], tuple(row["notify_at"]))
        for row in neo4j_session.run(
            "MATCH (m:SnowflakeResourceMonitor) RETURN m.id AS id, "
            "m.notify_at AS notify_at",
        )
    } == {
        (PLANT_BUDGET_MONITOR_ID, (75, 90)),
        (DUFF_MONITOR_ID, (50,)),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeResourceMonitor",
        "id",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (PLANT_BUDGET_MONITOR_ID, SNOWFLAKE_ACCOUNT_ID),
        (DUFF_MONITOR_ID, SNOWFLAKE_ACCOUNT_ID),
    }


def test_sync_snowflake_resource_monitors_unavailable(neo4j_session):
    # Arrange: an account whose role cannot run SHOW RESOURCE MONITORS.
    _ensure_local_neo4j_has_test_account(neo4j_session)

    # Act
    with patch.object(
        cartography.intel.snowflake.resource_monitors, "get", return_value=None
    ):
        complete = cartography.intel.snowflake.resource_monitors.sync(
            neo4j_session,
            build_test_client(),
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )

    # Assert: the sync reports itself incomplete so the caller skips cleanup rather
    # than deleting monitors it merely failed to read.
    assert complete is False
