from unittest.mock import patch

import cartography.intel.snowflake.session_policies
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.session_policies import SNOWFLAKE_SESSION_POLICIES
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
    cartography.intel.snowflake.session_policies,
    "get",
    return_value=SNOWFLAKE_SESSION_POLICIES,
)
def test_sync_snowflake_session_policies(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    seed_schema_level_dependencies(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.session_policies.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert
    assert complete is True
    # An unset UI timeout stays null rather than collapsing to zero, which would
    # read as "the session expires immediately".
    assert check_nodes(
        neo4j_session,
        "SnowflakeSessionPolicy",
        [
            "name",
            "session_idle_timeout_mins",
            "session_ui_idle_timeout_mins",
            "allowed_secondary_authentication_methods",
        ],
    ) == {
        ("SHORT_SESSIONS", 30, 10, "[PASSWORD]"),
        ("DEFAULT_SESSIONS", 240, None, None),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSessionPolicy",
        "name",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("SHORT_SESSIONS", SNOWFLAKE_ACCOUNT_ID),
        ("DEFAULT_SESSIONS", SNOWFLAKE_ACCOUNT_ID),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSessionPolicy",
        "name",
        "SnowflakeSchema",
        "name",
        "CONTAINS",
        rel_direction_right=False,
    ) == {
        ("SHORT_SESSIONS", TEST_SCHEMA_NAME),
        ("DEFAULT_SESSIONS", TEST_SCHEMA_NAME),
    }
