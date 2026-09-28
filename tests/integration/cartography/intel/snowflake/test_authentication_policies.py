from unittest.mock import patch

import cartography.intel.snowflake.authentication_policies
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.authentication_policies import (
    SNOWFLAKE_AUTHENTICATION_POLICIES,
)
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
    cartography.intel.snowflake.authentication_policies,
    "get",
    return_value=SNOWFLAKE_AUTHENTICATION_POLICIES,
)
def test_sync_snowflake_authentication_policies(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    seed_schema_level_dependencies(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.authentication_policies.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert
    assert complete is True
    # A policy that accepts a method but enforces MFA on none of them is the posture
    # gap this surface exists to expose.
    assert check_nodes(
        neo4j_session,
        "SnowflakeAuthenticationPolicy",
        ["name", "mfa_enrollment", "mfa_authentication_methods", "pat_policy"],
    ) == {
        ("REQUIRE_MFA", "REQUIRED", "[PASSWORD]", None),
        (
            "SERVICE_AUTH",
            "OPTIONAL",
            None,
            "NETWORK_POLICY_EVALUATION = ENFORCED_REQUIRED",
        ),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAuthenticationPolicy",
        "name",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("REQUIRE_MFA", SNOWFLAKE_ACCOUNT_ID),
        ("SERVICE_AUTH", SNOWFLAKE_ACCOUNT_ID),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAuthenticationPolicy",
        "name",
        "SnowflakeSchema",
        "name",
        "CONTAINS",
        rel_direction_right=False,
    ) == {
        ("REQUIRE_MFA", TEST_SCHEMA_NAME),
        ("SERVICE_AUTH", TEST_SCHEMA_NAME),
    }


@patch.object(
    cartography.intel.snowflake.authentication_policies, "get", return_value=[]
)
def test_sync_treats_an_account_with_no_policies_as_complete(mock_get, neo4j_session):
    """An account with no authentication policies is complete, not unavailable.

    Snowflake answers the listing with a body carrying neither result metadata nor
    rows in that case, which the client normalises to an empty list, so the sync has
    to report success and let cleanup run.
    """
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run(
        "MATCH (policy:SnowflakeAuthenticationPolicy) DETACH DELETE policy",
    )
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.authentication_policies.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert
    assert complete is True
    assert check_nodes(neo4j_session, "SnowflakeAuthenticationPolicy", ["id"]) == set()
