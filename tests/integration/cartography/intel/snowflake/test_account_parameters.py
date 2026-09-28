from unittest.mock import patch

import cartography.intel.snowflake.account_parameters
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.account_parameters import SNOWFLAKE_ACCOUNT_PARAMETERS
from tests.data.snowflake.account_parameters import SNOWFLAKE_NETWORK_POLICY_PARAMETERS
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


@patch.object(
    cartography.intel.snowflake.account_parameters,
    "get_account_network_policy",
    return_value="PLANT_PERIMETER",
)
@patch.object(
    cartography.intel.snowflake.account_parameters,
    "get",
    return_value=SNOWFLAKE_ACCOUNT_PARAMETERS,
)
def test_sync_snowflake_account_parameters(mock_get, mock_policy, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    network_policy, complete = cartography.intel.snowflake.account_parameters.sync(
        neo4j_session, client, common_job_parameters
    )

    # Assert
    assert complete is True
    # The network policy value is handed back so the network policy sync can attach
    # the policy to the account.
    assert network_policy == "PLANT_PERIMETER"

    # Only the security-relevant parameters become nodes; the statement timeout is
    # deliberately left out.
    assert check_nodes(
        neo4j_session,
        "SnowflakeAccountParameter",
        ["name", "value", "is_default"],
    ) == {
        ("NETWORK_POLICY", "PLANT_PERIMETER", False),
        ("PREVENT_UNLOAD_TO_INLINE_URL", "false", True),
        ("REQUIRE_STORAGE_INTEGRATION_FOR_STAGE_CREATION", "true", False),
    }

    # An empty level means nobody ever set the parameter, and has to read as null.
    assert check_nodes(
        neo4j_session, "SnowflakeAccountParameter", ["name", "level"]
    ) == {
        ("NETWORK_POLICY", "ACCOUNT"),
        ("PREVENT_UNLOAD_TO_INLINE_URL", None),
        ("REQUIRE_STORAGE_INTEGRATION_FOR_STAGE_CREATION", "ACCOUNT"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccountParameter",
        "name",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("NETWORK_POLICY", SNOWFLAKE_ACCOUNT_ID),
        ("PREVENT_UNLOAD_TO_INLINE_URL", SNOWFLAKE_ACCOUNT_ID),
        (
            "REQUIRE_STORAGE_INTEGRATION_FOR_STAGE_CREATION",
            SNOWFLAKE_ACCOUNT_ID,
        ),
    }


def test_get_account_network_policy_reads_the_filtered_listing(mocker):
    """The account-level policy is only stated by the NETWORK_POLICY parameter."""
    # Arrange
    client = build_test_client()
    client.run_sql = mocker.Mock(return_value=SNOWFLAKE_NETWORK_POLICY_PARAMETERS)

    # Act
    network_policy = (
        cartography.intel.snowflake.account_parameters.get_account_network_policy(
            client
        )
    )

    # Assert
    assert network_policy == "PLANT_PERIMETER"


@patch.object(
    cartography.intel.snowflake.account_parameters,
    "get_account_network_policy",
    return_value=None,
)
@patch.object(cartography.intel.snowflake.account_parameters, "get", return_value=None)
def test_sync_reports_incomplete_when_parameters_cannot_be_read(
    mock_get, mock_policy, neo4j_session
):
    """Losing the listing must not delete the parameters collected on an earlier run."""
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run(
        "MATCH (parameter:SnowflakeAccountParameter) DETACH DELETE parameter",
    )
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    network_policy, complete = cartography.intel.snowflake.account_parameters.sync(
        neo4j_session, client, common_job_parameters
    )

    # Assert
    assert complete is False
    assert network_policy is None
    assert check_nodes(neo4j_session, "SnowflakeAccountParameter", ["id"]) == set()
