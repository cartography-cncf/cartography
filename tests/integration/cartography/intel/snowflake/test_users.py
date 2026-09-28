from unittest.mock import patch

import cartography.intel.snowflake.users
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.users import SNOWFLAKE_SHOW_USERS
from tests.data.snowflake.users import SNOWFLAKE_USERS
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def _ensure_local_neo4j_has_test_users(neo4j_session) -> None:
    humans, services = cartography.intel.snowflake.users.transform(
        SNOWFLAKE_USERS,
        {row["name"]: row["has_mfa"] == "true" for row in SNOWFLAKE_SHOW_USERS},
        SNOWFLAKE_ACCOUNT_ID,
    )
    cartography.intel.snowflake.users.load_users(
        neo4j_session, humans, services, SNOWFLAKE_ACCOUNT_ID, TEST_UPDATE_TAG
    )


def _seed_network_policy(neo4j_session) -> None:
    """Minimal network policy node so the user's GOVERNED_BY edge can match."""
    neo4j_session.run(
        """
        MERGE (p:SnowflakeNetworkPolicy {id: $id})
        SET p.name = $name, p.lastupdated = $update_tag
        """,
        id=f"{SNOWFLAKE_ACCOUNT_ID}/network_policy/PLANT_PERIMETER",
        name="PLANT_PERIMETER",
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.snowflake.users,
    "get_mfa_enrollment",
    return_value={
        row["name"]: row["has_mfa"] == "true" for row in SNOWFLAKE_SHOW_USERS
    },
)
@patch.object(cartography.intel.snowflake.users, "get", return_value=SNOWFLAKE_USERS)
def test_sync_snowflake_users(mock_get, mock_mfa, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _seed_network_policy(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    cartography.intel.snowflake.users.sync(neo4j_session, client, common_job_parameters)

    # Assert: humans land on SnowflakeUser, with MFA enrollment merged in from SQL.
    assert check_nodes(
        neo4j_session, "SnowflakeUser", ["name", "has_mfa", "disabled", "has_password"]
    ) == {
        ("HOMER", False, False, True),
        ("BURNS", True, False, True),
        ("SMITHERS", False, True, True),
    }

    # Assert: the service user is a separate label, so ontology projections for
    # humans and machine identities do not contaminate each other.
    assert check_nodes(
        neo4j_session,
        "SnowflakeServiceUser",
        ["name", "user_type", "has_password", "has_rsa_public_key"],
    ) == {("SCRAM_BOT", "SERVICE", False, True)}

    # Assert the ontology split.
    assert {("HOMER",), ("BURNS",), ("SMITHERS",)} <= check_nodes(
        neo4j_session, "UserAccount", ["name"]
    )
    assert ("SCRAM_BOT",) in check_nodes(neo4j_session, "ServiceAccount", ["name"])
    # A service user must NOT be a UserAccount, or cross-provider human-identity
    # queries would count robots as people.
    assert ("SCRAM_BOT",) not in check_nodes(neo4j_session, "UserAccount", ["name"])

    # Assert the ontology normalization actually landed, so cross-provider identity
    # queries can read Snowflake users the same way they read Entra or Okta ones.
    # `active` is the inverse of Snowflake's `disabled`.
    assert check_nodes(
        neo4j_session,
        "SnowflakeUser",
        ["name", "_ont_username", "_ont_has_mfa", "_ont_active"],
    ) == {
        ("HOMER", "HOMER", False, True),
        ("BURNS", "BURNS", True, True),
        ("SMITHERS", "SMITHERS", False, False),
    }
    assert check_nodes(
        neo4j_session, "SnowflakeServiceUser", ["name", "_ont_name", "_ont_active"]
    ) == {("SCRAM_BOT", "SCRAM_BOT", True)}

    # Assert the MFA bypass window is captured; it is the reason to look at all.
    assert check_nodes(
        neo4j_session, "SnowflakeUser", ["name", "mins_to_bypass_mfa"]
    ) >= {("BURNS", 30)}

    # Assert every user hangs off the account tenant.
    assert check_rels(
        neo4j_session, "SnowflakeAccount", "id", "SnowflakeUser", "name", "RESOURCE"
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, "HOMER"),
        (SNOWFLAKE_ACCOUNT_ID, "BURNS"),
        (SNOWFLAKE_ACCOUNT_ID, "SMITHERS"),
    }

    # Assert the per-user network policy attachment, and that a user without one
    # gets no edge rather than an edge to a nonexistent node.
    assert check_rels(
        neo4j_session,
        "SnowflakeUser",
        "name",
        "SnowflakeNetworkPolicy",
        "name",
        "GOVERNED_BY",
    ) == {("HOMER", "PLANT_PERIMETER")}


def test_transform_treats_a_null_user_type_as_human():
    # Arrange: Snowflake leaves `type` unset for users created without one, and a
    # real account showed exactly that for its human admin.
    users = [{"name": "LENNY", "type": None}]

    # Act
    humans, services = cartography.intel.snowflake.users.transform(
        users, {}, SNOWFLAKE_ACCOUNT_ID
    )

    # Assert
    assert [user["name"] for user in humans] == ["LENNY"]
    assert services == []


def test_transform_leaves_mfa_null_when_it_could_not_be_read():
    # Arrange: SHOW USERS was not permitted, so enrollment is unknown.
    # Act
    humans, _ = cartography.intel.snowflake.users.transform(
        SNOWFLAKE_USERS, {}, SNOWFLAKE_ACCOUNT_ID
    )

    # Assert: unknown must stay null. Reporting false would claim every user is
    # unprotected, which is worse than admitting ignorance.
    assert {user["has_mfa"] for user in humans} == {None}


def test_transform_does_not_carry_the_redacted_password():
    # Arrange: the API returns `password: "********"`, which is not information.
    # Act
    humans, _ = cartography.intel.snowflake.users.transform(
        SNOWFLAKE_USERS, {}, SNOWFLAKE_ACCOUNT_ID
    )

    # Assert
    assert all("password" not in user for user in humans)
