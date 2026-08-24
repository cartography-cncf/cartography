from unittest.mock import patch

import cartography.intel.snowflake.notebooks
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.notebooks import SNOWFLAKE_NOTEBOOKS
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


@patch.object(
    cartography.intel.snowflake.notebooks, "get", return_value=SNOWFLAKE_NOTEBOOKS
)
def test_sync_snowflake_notebooks(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    seed_schema_level_dependencies(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.notebooks.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert
    assert complete is True
    assert check_nodes(
        neo4j_session, "SnowflakeNotebook", ["name", "title", "default_version"]
    ) == {
        ("REACTOR_FORECAST", "Reactor forecast", "LIVE"),
        ("DONUT_TRENDS", None, "VERSION$1"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeNotebook",
        "name",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, "REACTOR_FORECAST"),
        (SNOWFLAKE_ACCOUNT_ID, "DONUT_TRENDS"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "name",
        "SnowflakeNotebook",
        "name",
        "CONTAINS",
    ) == {
        (TEST_SCHEMA_NAME, "REACTOR_FORECAST"),
        (TEST_SCHEMA_NAME, "DONUT_TRENDS"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeNotebook",
        "name",
        "SnowflakeWarehouse",
        "name",
        "USES_WAREHOUSE",
    ) == {("REACTOR_FORECAST", "SECTOR_7G_WH")}

    assert check_rels(
        neo4j_session,
        "SnowflakeNotebook",
        "name",
        "SnowflakeComputePool",
        "name",
        "RUNS_ON",
    ) == {("REACTOR_FORECAST", "DONUT_POOL")}

    assert check_rels(
        neo4j_session,
        "SnowflakeNotebook",
        "name",
        "SnowflakeExternalAccessIntegration",
        "name",
        "USES_INTEGRATION",
    ) == {("REACTOR_FORECAST", "DUFF_EAI")}
