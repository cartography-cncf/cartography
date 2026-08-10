from unittest.mock import patch

import cartography.intel.snowflake.account_usage
import cartography.intel.snowflake.database_roles
import cartography.intel.snowflake.grants
import cartography.intel.snowflake.roles
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.roles import SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_ROLES
from tests.data.snowflake.roles import SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_USERS
from tests.data.snowflake.roles import SNOWFLAKE_ACCOUNT_USAGE_QUOTED_DATABASE_ROLE
from tests.data.snowflake.roles import (
    SNOWFLAKE_ACCOUNT_USAGE_QUOTED_DATABASE_ROLE_GRANTS,
)
from tests.data.snowflake.roles import SNOWFLAKE_ACCOUNT_USAGE_ROLES
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


def _clear_grant_edges(neo4j_session) -> None:
    """Delete every edge the grant sync produces.

    The ``neo4j_session`` fixture is module-scoped and only wipes at teardown, so a
    test asserting which edges *this* sync built has to start from none. Without
    this, an earlier test's edges satisfy the assertion and the test proves nothing:
    that is exactly how the ACCOUNT_USAGE path passed while dropping the whole role
    hierarchy, because the object-API test above had already created the edges.
    """
    neo4j_session.run(
        "MATCH ()-[r:HAS_ROLE|INCLUDES|HAS_PRIVILEGE]->() DELETE r",
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
    """The per-role object API path, selected when ACCOUNT_USAGE is unreadable."""
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
        use_account_usage=False,
    )

    # Assert: every edge is built, but the walk never claims completeness. SHOW GRANTS
    # only reports what the collector role can see, and a role it cannot see produces
    # no row and no error, so cleanup must not run off the back of this path.
    assert complete is False

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
        {"SYSADMIN": SNOWFLAKE_ROLE_GRANTS["SYSADMIN"]}, set(), SNOWFLAKE_ACCOUNT_ID
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
        set(),
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
        use_account_usage=False,
    )

    # Assert: the caller must skip grant cleanup, or edges it merely failed to
    # re-read this run would be deleted.
    assert complete is False


@patch.object(
    cartography.intel.snowflake.account_usage,
    "get_grants_to_users",
    return_value=SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_USERS,
)
@patch.object(
    cartography.intel.snowflake.account_usage,
    "get_grants_to_roles",
    return_value=SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_ROLES,
)
def test_sync_snowflake_grants_from_account_usage(
    mock_to_roles, mock_to_users, neo4j_session
):
    """The ACCOUNT_USAGE path builds the same graph, and may claim completeness.

    Two queries replace the per-role walk. Because the views are account-wide rather
    than filtered by what the collector role can see, this is the only path that can
    honestly report a complete grant graph and so let cleanup run.
    """
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    roles = _ensure_local_neo4j_has_test_roles(neo4j_session)
    _seed_grant_targets(neo4j_session)
    _clear_grant_edges(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.grants.sync(
        neo4j_session,
        client,
        roles,
        service_user_names={"SCRAM_BOT"},
        database_roles=[],
        common_job_parameters={
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
        },
    )

    # Assert
    assert complete is True
    # The role hierarchy comes out of GRANTS_TO_ROLES, where `GRANT ROLE a TO ROLE b`
    # is recorded as USAGE on ROLE a held by b.
    assert check_rels(
        neo4j_session, "SnowflakeRole", "name", "SnowflakeRole", "name", "INCLUDES"
    ) == {
        ("ACCOUNTADMIN", "SYSADMIN"),
        ("SYSADMIN", "SAFETY_INSPECTOR"),
    }
    # User assignments come out of GRANTS_TO_USERS, and still split by principal kind.
    assert check_rels(
        neo4j_session, "SnowflakeUser", "name", "SnowflakeRole", "name", "HAS_ROLE"
    ) == {
        ("BURNS", "ACCOUNTADMIN"),
        ("HOMER", "SAFETY_INSPECTOR"),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeServiceUser",
        "name",
        "SnowflakeRole",
        "name",
        "HAS_ROLE",
    ) == {("SCRAM_BOT", "REACTOR_READER")}
    # Privilege edges resolve the same way, including the account-level one.
    assert check_rels(
        neo4j_session,
        "SnowflakeRole",
        "name",
        "SnowflakeAccount",
        "id",
        "HAS_PRIVILEGE",
    ) == {("SYSADMIN", SNOWFLAKE_ACCOUNT_ID)}
    assert check_rels(
        neo4j_session,
        "SnowflakeRole",
        "name",
        "SnowflakeTable",
        "name",
        "HAS_PRIVILEGE",
    ) == {("SAFETY_INSPECTOR", "REACTOR_READINGS")}


@patch.object(
    cartography.intel.snowflake.account_usage,
    "get_grants_to_users",
    return_value=None,
)
@patch.object(
    cartography.intel.snowflake.account_usage,
    "get_grants_to_roles",
    return_value=None,
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
def test_sync_falls_back_to_the_object_api_when_account_usage_is_unreadable(
    mock_grants, mock_grants_of, mock_to_roles, mock_to_users, neo4j_session
):
    """An unreadable ACCOUNT_USAGE must degrade to the REST walk, not to nothing."""
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    roles = _ensure_local_neo4j_has_test_roles(neo4j_session)
    _seed_grant_targets(neo4j_session)
    _clear_grant_edges(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.grants.sync(
        neo4j_session,
        client,
        roles,
        service_user_names={"SCRAM_BOT"},
        database_roles=[],
        common_job_parameters={
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
        },
    )

    # Assert: the edges are still built from the object API, but completeness is not
    # claimed, so cleanup stays off.
    assert complete is False
    assert check_rels(
        neo4j_session, "SnowflakeRole", "name", "SnowflakeRole", "name", "INCLUDES"
    ) == {
        ("ACCOUNTADMIN", "SYSADMIN"),
        ("SYSADMIN", "SAFETY_INSPECTOR"),
    }


@patch.object(cartography.intel.snowflake.roles, "get")
def test_roles_sync_prefers_account_usage_and_reports_complete(mock_get, neo4j_session):
    """ACCOUNT_USAGE is authoritative, so the roles sync may claim completeness."""
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run("MATCH (r:SnowflakeRole) DETACH DELETE r")

    # Act
    roles, complete = cartography.intel.snowflake.roles.sync(
        neo4j_session,
        client,
        SNOWFLAKE_ACCOUNT_USAGE_ROLES,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the object API is never called, only ROLE_TYPE='ROLE' rows become
    # account roles, and the application role is left out entirely.
    mock_get.assert_not_called()
    assert complete is True
    assert check_nodes(neo4j_session, "SnowflakeRole", ["name"]) == {
        ("ACCOUNTADMIN",),
        ("SYSADMIN",),
        ("SAFETY_INSPECTOR",),
        ("REACTOR_READER",),
    }
    assert len(roles) == 4


def test_roles_sync_reports_incomplete_on_the_object_api(neo4j_session, mocker):
    """SHOW ROLES visibility means the object API can never claim completeness.

    This is the regression guard: reporting True here is what let cleanup delete
    roles the collector could not see.
    """
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    mocker.patch.object(
        cartography.intel.snowflake.roles, "get", return_value=SNOWFLAKE_ROLES
    )

    # Act
    _, complete = cartography.intel.snowflake.roles.sync(
        neo4j_session,
        client,
        None,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is False


@patch.object(cartography.intel.snowflake.database_roles, "get")
def test_database_roles_sync_reads_account_usage_for_every_database(
    mock_get, neo4j_session
):
    """The database-role half of the same view, covering databases this run cannot walk."""
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run("MATCH (r:SnowflakeDatabaseRole) DETACH DELETE r")

    # Act: no walkable databases at all, which on the object API path would mean no
    # database roles could be enumerated.
    database_roles, complete = cartography.intel.snowflake.database_roles.sync(
        neo4j_session,
        client,
        [],
        SNOWFLAKE_ACCOUNT_USAGE_ROLES,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the database role is still found, qualified by its database, and no
    # per-database request was made.
    mock_get.assert_not_called()
    assert complete is True
    assert check_nodes(
        neo4j_session, "SnowflakeDatabaseRole", ["name", "qualified_name"]
    ) == {("TELEMETRY_READER", "SPRINGFIELD_DB.TELEMETRY_READER")}
    assert len(database_roles) == 1


def test_both_grant_paths_produce_the_same_edges():
    """The two sources must agree, or the fallback silently changes the graph.

    The ACCOUNT_USAGE fixture describes the same account as the REST fixture, so
    running each through its own reshaping and then the shared transform has to yield
    identical edge sets. This is what stops the two paths drifting apart.
    """
    # Arrange
    rest_grants, _ = cartography.intel.snowflake.grants.transform_grants(
        SNOWFLAKE_ROLE_GRANTS, set(), SNOWFLAKE_ACCOUNT_ID
    )
    account_usage_by_role, _ = cartography.intel.snowflake.account_usage.split_grants(
        SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_ROLES, []
    )

    # Act
    usage_grants, _ = cartography.intel.snowflake.grants.transform_grants(
        account_usage_by_role, set(), SNOWFLAKE_ACCOUNT_ID
    )

    # Assert: the same (principal, securable, privileges) triples from both sources.
    # The REST fixture carries one grant on an object type Cartography does not model,
    # which both paths drop, so it is absent from each side rather than excluded here.
    def as_set(edges):
        return {
            (edge["principal_id"], edge["securable_id"], tuple(edge["privileges"]))
            for edge in edges
        }

    # The role-hierarchy USAGE-on-ROLE rows only exist in the ACCOUNT_USAGE view, so
    # compare the object privileges the two sources both describe.
    role_securables = {
        f"{SNOWFLAKE_ACCOUNT_ID}/role/SYSADMIN",
        f"{SNOWFLAKE_ACCOUNT_ID}/role/SAFETY_INSPECTOR",
    }
    assert as_set(rest_grants) == {
        edge for edge in as_set(usage_grants) if edge[1] not in role_securables
    }


@patch.object(
    cartography.intel.snowflake.account_usage,
    "get_grants_to_users",
    return_value=[],
)
@patch.object(
    cartography.intel.snowflake.account_usage,
    "get_grants_to_roles",
    return_value=SNOWFLAKE_ACCOUNT_USAGE_QUOTED_DATABASE_ROLE_GRANTS,
)
def test_quoted_database_role_keeps_its_grant_edges(
    mock_to_roles, mock_to_users, neo4j_session
):
    """A database role created with a quoted, lowercase name must still resolve.

    ACCOUNT_USAGE reports the pair unquoted (`springfield_db.telemetry_peek`) while
    the node id is built through sf_fqn as `"springfield_db"."telemetry_peek"`. Without
    requalifying, the principal never matches and the privilege edge vanishes.
    """
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _seed_grant_targets(neo4j_session)
    _clear_grant_edges(neo4j_session)
    database_roles = cartography.intel.snowflake.database_roles.transform(
        cartography.intel.snowflake.account_usage.split_roles(
            SNOWFLAKE_ACCOUNT_USAGE_QUOTED_DATABASE_ROLE
        )[1],
        SNOWFLAKE_ACCOUNT_ID,
    )
    cartography.intel.snowflake.database_roles.load_database_roles(
        neo4j_session, database_roles, SNOWFLAKE_ACCOUNT_ID, TEST_UPDATE_TAG
    )

    # Act
    cartography.intel.snowflake.grants.sync(
        neo4j_session,
        client,
        [],
        service_user_names=set(),
        database_roles=database_roles,
        common_job_parameters={
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
        },
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "SnowflakeDatabaseRole",
        "qualified_name",
        "SnowflakeTable",
        "name",
        "HAS_PRIVILEGE",
    ) == {('"springfield_db"."telemetry_peek"', "REACTOR_READINGS")}
