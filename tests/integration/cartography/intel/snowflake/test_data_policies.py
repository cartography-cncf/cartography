from unittest.mock import patch

import cartography.intel.snowflake.data_policies
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.data_policies import SNOWFLAKE_DATA_POLICIES
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
    cartography.intel.snowflake.data_policies,
    "get",
    return_value=SNOWFLAKE_DATA_POLICIES,
)
def test_sync_snowflake_data_policies(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    seed_schema_level_dependencies(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.data_policies.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert
    assert complete is True
    # All five governance kinds share one label and are told apart by policy_kind,
    # which is also the discriminator the attachment view reports.
    assert check_nodes(
        neo4j_session,
        "SnowflakeDataPolicy",
        ["name", "policy_kind"],
    ) == {
        ("MASK_EMPLOYEE_ID", "MASKING_POLICY"),
        ("SECTOR_ROWS", "ROW_ACCESS_POLICY"),
        ("NO_PROJECT_BADGE", "PROJECTION_POLICY"),
    }

    # A kind whose listing omits the body column keeps a null body rather than an
    # empty string.
    assert check_nodes(neo4j_session, "SnowflakeDataPolicy", ["name", "body"]) == {
        (
            "MASK_EMPLOYEE_ID",
            "CASE WHEN CURRENT_ROLE() = 'SAFETY_INSPECTOR' THEN '***' ELSE VAL END",
        ),
        ("SECTOR_ROWS", "SECTOR = '7G'"),
        ("NO_PROJECT_BADGE", None),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeDataPolicy",
        "name",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("MASK_EMPLOYEE_ID", SNOWFLAKE_ACCOUNT_ID),
        ("SECTOR_ROWS", SNOWFLAKE_ACCOUNT_ID),
        ("NO_PROJECT_BADGE", SNOWFLAKE_ACCOUNT_ID),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeDataPolicy",
        "name",
        "SnowflakeSchema",
        "name",
        "CONTAINS",
        rel_direction_right=False,
    ) == {
        ("MASK_EMPLOYEE_ID", TEST_SCHEMA_NAME),
        ("SECTOR_ROWS", TEST_SCHEMA_NAME),
        ("NO_PROJECT_BADGE", TEST_SCHEMA_NAME),
    }


@patch.object(cartography.intel.snowflake.data_policies, "get", return_value=None)
def test_sync_reports_incomplete_on_a_standard_edition_account(mock_get, neo4j_session):
    """Standard-edition accounts genuinely error on these statements.

    The sync must then write nothing and report incomplete, so the caller skips
    cleanup instead of deleting policies collected while the account was on a higher
    edition.
    """
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run("MATCH (policy:SnowflakeDataPolicy) DETACH DELETE policy")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.data_policies.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert
    assert complete is False
    assert check_nodes(neo4j_session, "SnowflakeDataPolicy", ["id"]) == set()
