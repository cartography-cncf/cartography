from unittest.mock import patch

import cartography.intel.snowflake.password_policies
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.password_policies import SNOWFLAKE_PASSWORD_POLICIES
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
    cartography.intel.snowflake.password_policies,
    "get",
    return_value=SNOWFLAKE_PASSWORD_POLICIES,
)
def test_sync_snowflake_password_policies(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    seed_schema_level_dependencies(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.password_policies.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert
    assert complete is True
    # A zero max age disables rotation entirely, which is only visible because the
    # described settings are stored as numbers rather than as strings.
    assert check_nodes(
        neo4j_session,
        "SnowflakePasswordPolicy",
        ["name", "password_min_length", "password_max_age_days"],
    ) == {
        ("STRICT_PASSWORDS", 14, 90),
        ("LEGACY_PASSWORDS", 8, 0),
    }

    # A setting the DESCRIBE output did not report stays null instead of becoming
    # zero, which would read as "no retries allowed".
    assert check_nodes(
        neo4j_session,
        "SnowflakePasswordPolicy",
        ["name", "password_max_retries", "password_history"],
    ) == {
        ("STRICT_PASSWORDS", 5, 5),
        ("LEGACY_PASSWORDS", None, None),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakePasswordPolicy",
        "name",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("STRICT_PASSWORDS", SNOWFLAKE_ACCOUNT_ID),
        ("LEGACY_PASSWORDS", SNOWFLAKE_ACCOUNT_ID),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakePasswordPolicy",
        "name",
        "SnowflakeSchema",
        "name",
        "CONTAINS",
        rel_direction_right=False,
    ) == {
        ("STRICT_PASSWORDS", TEST_SCHEMA_NAME),
        ("LEGACY_PASSWORDS", TEST_SCHEMA_NAME),
    }
