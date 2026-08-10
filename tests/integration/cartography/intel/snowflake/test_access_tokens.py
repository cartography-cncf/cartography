from unittest.mock import patch

import cartography.intel.snowflake.access_tokens
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from tests.data.snowflake.access_tokens import SNOWFLAKE_ACCESS_TOKENS
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_grants import (
    _ensure_local_neo4j_has_test_roles,
)
from tests.integration.cartography.intel.snowflake.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

# What `users.sync()` hands to the token sync: the name Snowflake reports the token
# against, plus the node id the user was actually loaded under.
TEST_USERS = [
    {"name": name, "id": sf_id(SNOWFLAKE_ACCOUNT_ID, "user", name)}
    for name in ("HOMER", "BURNS", "SCRAM_BOT", "SMITHERS")
]


def _tokens_for_user(client, user_name):
    """Stand in for the per-user SHOW, which only ever returns that user's tokens."""
    return [
        token for token in SNOWFLAKE_ACCESS_TOKENS if token["user_name"] == user_name
    ]


def _token_id(user_name: str, name: str) -> str:
    return sf_id(SNOWFLAKE_ACCOUNT_ID, "access_token", sf_fqn(user_name, name))


@patch.object(
    cartography.intel.snowflake.access_tokens,
    "get_for_user",
    side_effect=_tokens_for_user,
)
def test_sync_snowflake_access_tokens(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_roles(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.access_tokens.sync(
        neo4j_session, client, TEST_USERS, common_job_parameters
    )

    # Assert
    assert complete is True
    # A non-null bypass window is a live exemption from the network policy, so it has
    # to survive as a number rather than as the string the SQL API returned.
    assert check_nodes(
        neo4j_session,
        "SnowflakeProgrammaticAccessToken",
        ["name", "status", "mins_to_bypass_required_network_policy"],
    ) == {
        ("donut_dashboard", "ACTIVE", 477),
        ("scram_ingest", "ACTIVE", None),
        ("retired_contractor", "EXPIRED", None),
    }

    # The ontology label is what makes a token discoverable as a credential across
    # providers.
    assert check_nodes(neo4j_session, "APIKey", ["id"]) == {
        (_token_id("HOMER", "donut_dashboard"),),
        (_token_id("SCRAM_BOT", "scram_ingest"),),
        (_token_id("SMITHERS", "retired_contractor"),),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeProgrammaticAccessToken",
        "name",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("donut_dashboard", SNOWFLAKE_ACCOUNT_ID),
        ("scram_ingest", SNOWFLAKE_ACCOUNT_ID),
        ("retired_contractor", SNOWFLAKE_ACCOUNT_ID),
    }

    # A token owned by a service user is the case the ontology constraint pins down:
    # an API key owned by a service account has to use OWNED_BY.
    assert check_rels(
        neo4j_session,
        "SnowflakeProgrammaticAccessToken",
        "name",
        "SnowflakeServiceUser",
        "name",
        "OWNED_BY",
        rel_direction_right=True,
    ) == {("scram_ingest", "SCRAM_BOT")}

    assert check_rels(
        neo4j_session,
        "SnowflakeProgrammaticAccessToken",
        "name",
        "SnowflakeUser",
        "name",
        "OWNED_BY",
        rel_direction_right=True,
    ) == {
        ("donut_dashboard", "HOMER"),
        # An expired token still owned by a disabled user: worth seeing in the graph.
        ("retired_contractor", "SMITHERS"),
    }

    # Only the restricted token is confined to a role; the unrestricted ones inherit
    # every role their user holds and so get no edge.
    assert check_rels(
        neo4j_session,
        "SnowflakeProgrammaticAccessToken",
        "name",
        "SnowflakeRole",
        "name",
        "RESTRICTED_TO",
        rel_direction_right=True,
    ) == {("scram_ingest", "SAFETY_INSPECTOR")}


@patch.object(
    cartography.intel.snowflake.access_tokens, "get_for_user", return_value=None
)
def test_sync_reports_incomplete_when_tokens_cannot_be_read(mock_get, neo4j_session):
    """An unreadable surface must report incomplete and write nothing.

    That is what makes the caller skip cleanup, which is the only thing standing
    between a permission change and the deletion of still-valid tokens.
    """
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run(
        "MATCH (token:SnowflakeProgrammaticAccessToken) DETACH DELETE token",
    )
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.access_tokens.sync(
        neo4j_session, client, TEST_USERS, common_job_parameters
    )

    # Assert
    assert complete is False
    assert (
        check_nodes(neo4j_session, "SnowflakeProgrammaticAccessToken", ["id"]) == set()
    )
