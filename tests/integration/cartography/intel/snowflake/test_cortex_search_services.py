from unittest.mock import patch

import cartography.intel.snowflake.cortex_search_services
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.cortex_search_services import SNOWFLAKE_CORTEX_SEARCH_SERVICES
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
    cartography.intel.snowflake.cortex_search_services,
    "get",
    return_value=SNOWFLAKE_CORTEX_SEARCH_SERVICES,
)
def test_sync_snowflake_cortex_search_services(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    seed_schema_level_dependencies(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.cortex_search_services.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeCortexSearchService",
        ["name", "target_lag", "search_column"],
    ) == {
        ("REACTOR_LOG_SEARCH", "1 hour", "OPERATOR_NOTES"),
        ("SAFETY_MEMO_SEARCH", "1 day", "MEMO_TEXT"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeCortexSearchService",
        "name",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, "REACTOR_LOG_SEARCH"),
        (SNOWFLAKE_ACCOUNT_ID, "SAFETY_MEMO_SEARCH"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "name",
        "SnowflakeCortexSearchService",
        "name",
        "CONTAINS",
    ) == {
        (TEST_SCHEMA_NAME, "REACTOR_LOG_SEARCH"),
        (TEST_SCHEMA_NAME, "SAFETY_MEMO_SEARCH"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeCortexSearchService",
        "name",
        "SnowflakeWarehouse",
        "name",
        "USES_WAREHOUSE",
    ) == {("REACTOR_LOG_SEARCH", "SECTOR_7G_WH")}

    # Only the service defined over a named table resolves; the one defined over a
    # query has no object to point at.
    assert check_rels(
        neo4j_session,
        "SnowflakeCortexSearchService",
        "name",
        "SnowflakeTable",
        "name",
        "READS_FROM",
    ) == {("REACTOR_LOG_SEARCH", "REACTOR_READINGS")}
