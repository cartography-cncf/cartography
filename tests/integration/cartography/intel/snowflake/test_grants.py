from unittest.mock import patch

import cartography.intel.snowflake.grants
import cartography.intel.snowflake.roles
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.roles import SNOWFLAKE_ROLE_GRANTS
from tests.data.snowflake.roles import SNOWFLAKE_ROLE_GRANTS_OF
from tests.data.snowflake.roles import SNOWFLAKE_ROLES
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


def _ensure_local_neo4j_has_test_roles(neo4j_session) -> list[dict]:
    roles = cartography.intel.snowflake.roles.transform(
        SNOWFLAKE_ROLES, SNOWFLAKE_ACCOUNT_ID
    )
    cartography.intel.snowflake.roles.load_roles(
        neo4j_session, roles, SNOWFLAKE_ACCOUNT_ID, TEST_UPDATE_TAG
    )
    return roles


def _seed_grant_targets(neo4j_session) -> None:
    """Seed the database and table that SAFETY_INSPECTOR holds privileges on."""
    neo4j_session.run(
        """
        MERGE (d:SnowflakeDatabase:SnowflakeSecurable {id: $db_id})
          SET d.name = 'SPRINGFIELD_DB', d.lastupdated = $update_tag
        MERGE (t:SnowflakeTable:SnowflakeSecurable {id: $table_id})
          SET t.name = 'REACTOR_READINGS', t.lastupdated = $update_tag
        """,
        db_id=f"{SNOWFLAKE_ACCOUNT_ID}/database/SPRINGFIELD_DB",
        table_id=(
            f"{SNOWFLAKE_ACCOUNT_ID}/table/SPRINGFIELD_DB.NUCLEAR_PLANT.REACTOR_READINGS"
        ),
        update_tag=TEST_UPDATE_TAG,
    )


def test_sync_snowflake_roles(neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_account(neo4j_session)

    # Act
    _ensure_local_neo4j_has_test_roles(neo4j_session)

    # Assert: builtin roles are distinguished from customer-defined ones, because
    # reaching a builtin admin role is the end of most escalation paths.
    assert check_nodes(neo4j_session, "SnowflakeRole", ["name", "role_type"]) == {
        ("ACCOUNTADMIN", "BUILTIN"),
        ("SYSADMIN", "BUILTIN"),
        ("SAFETY_INSPECTOR", "CUSTOM"),
        ("REACTOR_READER", "CUSTOM"),
    }

    # Roles are PermissionRoles, so cross-provider role queries reach them.
    assert {("ACCOUNTADMIN",), ("SAFETY_INSPECTOR",)} <= check_nodes(
        neo4j_session, "PermissionRole", ["name"]
    )


@patch.object(
    cartography.intel.snowflake.grants,
    "get_role_grants_of",
    side_effect=lambda client, role: SNOWFLAKE_ROLE_GRANTS_OF.get(role, []),
)
@patch.object(
    cartography.intel.snowflake.grants,
    "get_role_grants",
    side_effect=lambda client, role: SNOWFLAKE_ROLE_GRANTS.get(role, []),
)
def test_sync_snowflake_grants(mock_grants, mock_grants_of, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    roles = _ensure_local_neo4j_has_test_roles(neo4j_session)
    _seed_grant_targets(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.grants.sync(
        neo4j_session,
        client,
        roles,
        service_user_names={"SCRAM_BOT"},
        database_roles=[],
        common_job_parameters=common_job_parameters,
    )

    # Assert the walk reported success, which is what allows cleanup to run.
    assert complete is True

    # Assert the role hierarchy. ACCOUNTADMIN inherits SYSADMIN which inherits
    # SAFETY_INSPECTOR, so the composite role is the edge source and privilege
    # flows upward.
    assert check_rels(
        neo4j_session, "SnowflakeRole", "name", "SnowflakeRole", "name", "INCLUDES"
    ) == {
        ("ACCOUNTADMIN", "SYSADMIN"),
        ("SYSADMIN", "SAFETY_INSPECTOR"),
    }

    # Assert human role assignments.
    assert check_rels(
        neo4j_session, "SnowflakeUser", "name", "SnowflakeRole", "name", "HAS_ROLE"
    ) == {
        ("BURNS", "ACCOUNTADMIN"),
        ("HOMER", "SAFETY_INSPECTOR"),
    }

    # Assert the service user's assignment lands on the service-user label.
    assert check_rels(
        neo4j_session,
        "SnowflakeServiceUser",
        "name",
        "SnowflakeRole",
        "name",
        "HAS_ROLE",
    ) == {("SCRAM_BOT", "REACTOR_READER")}

    # Assert account-level privileges attach to the account node, resolved despite
    # the payload naming the account by its locator.
    assert check_rels(
        neo4j_session,
        "SnowflakeRole",
        "name",
        "SnowflakeAccount",
        "id",
        "HAS_PRIVILEGE",
    ) == {("SYSADMIN", SNOWFLAKE_ACCOUNT_ID)}

    # Assert object-level privileges.
    assert check_rels(
        neo4j_session,
        "SnowflakeRole",
        "name",
        "SnowflakeTable",
        "name",
        "HAS_PRIVILEGE",
    ) == {("SAFETY_INSPECTOR", "REACTOR_READINGS")}


def test_transform_grants_aggregates_one_edge_per_object():
    # Arrange: the API returns one row per privilege, so SYSADMIN's three
    # account-level privileges arrive as three separate rows.
    # Act
    grants, unmodelled = cartography.intel.snowflake.grants.transform_grants(
        {"SYSADMIN": SNOWFLAKE_ROLE_GRANTS["SYSADMIN"]}, SNOWFLAKE_ACCOUNT_ID
    )

    # Assert they collapse into a single edge carrying a sorted privilege list,
    # which is what keeps the grant graph one-edge-per-pair and traversable.
    assert len(grants) == 1
    assert grants[0]["privileges"] == [
        "CREATE COMPUTE POOL",
        "CREATE DATABASE",
        "CREATE WAREHOUSE",
    ]
    # WITH GRANT OPTION on any one privilege makes the whole grant re-grantable.
    assert grants[0]["grant_option"] is True
    assert grants[0]["securable_id"] == SNOWFLAKE_ACCOUNT_ID
    assert unmodelled == 0


def test_transform_grants_counts_unmodelled_object_types():
    # Act
    grants, unmodelled = cartography.intel.snowflake.grants.transform_grants(
        {"SAFETY_INSPECTOR": SNOWFLAKE_ROLE_GRANTS["SAFETY_INSPECTOR"]},
        SNOWFLAKE_ACCOUNT_ID,
    )

    # Assert: a grant on an object type Cartography does not model is reported
    # rather than silently dropped, and never becomes a dangling edge.
    assert unmodelled == 1
    assert len(grants) == 2


def test_sync_reports_incomplete_when_a_role_cannot_be_read(neo4j_session, mocker):
    # Arrange: one role 403s, which must NOT be mistaken for "has no grants".
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    roles = _ensure_local_neo4j_has_test_roles(neo4j_session)
    mocker.patch.object(
        cartography.intel.snowflake.grants, "get_role_grants", return_value=None
    )
    mocker.patch.object(
        cartography.intel.snowflake.grants, "get_role_grants_of", return_value=[]
    )

    # Act
    complete = cartography.intel.snowflake.grants.sync(
        neo4j_session,
        client,
        roles,
        service_user_names=set(),
        database_roles=[],
        common_job_parameters={"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert: the caller must skip grant cleanup, or edges it merely failed to
    # re-read this run would be deleted.
    assert complete is False
