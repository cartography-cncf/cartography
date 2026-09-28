from unittest.mock import patch

import cartography.intel.snowflake.credentials
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.credentials import SNOWFLAKE_CREDENTIALS
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


@patch.object(
    cartography.intel.snowflake.credentials,
    "get",
    return_value=SNOWFLAKE_CREDENTIALS,
)
def test_sync_snowflake_credentials(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.credentials.sync(
        neo4j_session, client, common_job_parameters
    )

    # Assert
    assert complete is True
    # The credential type is the whole point of this surface: it is what separates a
    # password-only identity from one with a second factor.
    assert check_nodes(
        neo4j_session,
        "SnowflakeCredential",
        ["user_name", "credential_type"],
    ) == {
        ("HOMER", "PASSWORD"),
        ("HOMER", "TOTP"),
        ("SCRAM_BOT", "KEYPAIR"),
    }

    # An empty or absent expiration string means "never expires", and has to become
    # null rather than an epoch zero.
    never_expiring = neo4j_session.run(
        """
        MATCH (credential:SnowflakeCredential)
        WHERE credential.expiration_date IS NULL
        RETURN collect(credential.credential_type) AS types
        """,
    ).single()["types"]
    assert sorted(never_expiring) == ["PASSWORD", "TOTP"]

    assert check_rels(
        neo4j_session,
        "SnowflakeCredential",
        "credential_id",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("101", SNOWFLAKE_ACCOUNT_ID),
        ("102", SNOWFLAKE_ACCOUNT_ID),
        ("103", SNOWFLAKE_ACCOUNT_ID),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeCredential",
        "credential_id",
        "SnowflakeUser",
        "name",
        "OWNED_BY",
        rel_direction_right=True,
    ) == {("101", "HOMER"), ("102", "HOMER")}

    assert check_rels(
        neo4j_session,
        "SnowflakeCredential",
        "credential_id",
        "SnowflakeServiceUser",
        "name",
        "OWNED_BY",
        rel_direction_right=True,
    ) == {("103", "SCRAM_BOT")}


@patch.object(cartography.intel.snowflake.credentials, "get", return_value=None)
def test_sync_reports_incomplete_when_account_usage_is_unreadable(
    mock_get, neo4j_session
):
    """ACCOUNT_USAGE needs an extra grant, so losing it must not empty the graph."""
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run("MATCH (credential:SnowflakeCredential) DETACH DELETE credential")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.credentials.sync(
        neo4j_session, client, common_job_parameters
    )

    # Assert
    assert complete is False
    assert check_nodes(neo4j_session, "SnowflakeCredential", ["id"]) == set()
