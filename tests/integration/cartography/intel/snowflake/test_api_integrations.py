from unittest.mock import patch

import cartography.intel.snowflake.api_integrations
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.api_integrations import SNOWFLAKE_API_INTEGRATION_ROLE_ARN
from tests.data.snowflake.api_integrations import SNOWFLAKE_API_INTEGRATIONS
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

PLANT_GATEWAY_ID = "SPRINGFIELD.NUCLEAR/api_integration/PLANT_GATEWAY_INTEGRATION"
SPRINGFIELD_GIT_ID = "SPRINGFIELD.NUCLEAR/api_integration/SPRINGFIELD_GIT_INTEGRATION"


@patch.object(
    cartography.intel.snowflake.api_integrations,
    "get",
    return_value=SNOWFLAKE_API_INTEGRATIONS,
)
def test_sync_snowflake_api_integrations(mock_get, neo4j_session):
    # Arrange: the IAM role the external function assumes belongs to the aws module.
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run(
        "MERGE (p:AWSPrincipal{arn: $arn}) SET p.lastupdated = $tag",
        arn=SNOWFLAKE_API_INTEGRATION_ROLE_ARN,
        tag=TEST_UPDATE_TAG,
    )

    # Act
    complete = cartography.intel.snowflake.api_integrations.sync(
        neo4j_session,
        build_test_client(),
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the api_hook sub-object is flattened onto the node, so the hook type and
    # the assumed role are readable without a nested lookup.
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeApiIntegration",
        ["id", "name", "enabled", "api_hook_type", "api_provider", "api_aws_role_arn"],
    ) == {
        (
            PLANT_GATEWAY_ID,
            "PLANT_GATEWAY_INTEGRATION",
            True,
            "AWS",
            "aws_api_gateway",
            SNOWFLAKE_API_INTEGRATION_ROLE_ARN,
        ),
        (
            SPRINGFIELD_GIT_ID,
            "SPRINGFIELD_GIT_INTEGRATION",
            True,
            "GIT",
            "git_https_api",
            None,
        ),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeApiIntegration",
        "id",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (PLANT_GATEWAY_ID, SNOWFLAKE_ACCOUNT_ID),
        (SPRINGFIELD_GIT_ID, SNOWFLAKE_ACCOUNT_ID),
    }
    # The cross-cloud payoff: only the AWS-backed integration assumes a role, so only
    # it crosses into the AWS graph.
    assert check_rels(
        neo4j_session,
        "SnowflakeApiIntegration",
        "id",
        "AWSPrincipal",
        "arn",
        "ASSUMES_ROLE",
        rel_direction_right=True,
    ) == {(PLANT_GATEWAY_ID, SNOWFLAKE_API_INTEGRATION_ROLE_ARN)}
