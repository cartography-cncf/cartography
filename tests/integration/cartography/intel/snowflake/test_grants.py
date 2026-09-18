from unittest.mock import patch

import pytest

import cartography.intel.snowflake.account_usage
import cartography.intel.snowflake.database_roles
import cartography.intel.snowflake.grants
import cartography.intel.snowflake.roles
from cartography.intel.snowflake.inherited_grants import cleanup
from cartography.intel.snowflake.inherited_grants import load_grants
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


@pytest.fixture
def isolated_inherited_grants(neo4j_session):
    neo4j_session.run("MATCH (g:SnowflakeInheritedGrant) DETACH DELETE g").consume()
    try:
        yield
    finally:
        neo4j_session.run("MATCH (g:SnowflakeInheritedGrant) DETACH DELETE g").consume()


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
    complete, assignments_complete, inherited_complete = (
        cartography.intel.snowflake.grants.sync(
            neo4j_session,
            client,
            roles,
            service_user_names={"SCRAM_BOT"},
            database_roles=[],
            common_job_parameters=common_job_parameters,
            use_account_usage=False,
        )
    )

    # Assert: every edge is built, but the walk never claims completeness. SHOW GRANTS
    # only reports what the collector role can see, and a role it cannot see produces
    # no row and no error, so cleanup must not run off the back of this path.
    assert complete is False
    assert assignments_complete is False
    assert inherited_complete is False

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
    complete, assignments_complete, inherited_complete = (
        cartography.intel.snowflake.grants.sync(
            neo4j_session,
            client,
            roles,
            service_user_names=set(),
            database_roles=[],
            common_job_parameters={"UPDATE_TAG": TEST_UPDATE_TAG},
            use_account_usage=False,
        )
    )

    # Assert: the caller must skip grant cleanup, or edges it merely failed to
    # re-read this run would be deleted.
    assert complete is False
    assert assignments_complete is False
    assert inherited_complete is False


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
    complete, assignments_complete, inherited_complete = (
        cartography.intel.snowflake.grants.sync(
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
    )

    # Assert
    assert complete is True
    assert assignments_complete is True
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
    complete, assignments_complete, inherited_complete = (
        cartography.intel.snowflake.grants.sync(
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
    )

    # Assert: the edges are still built from the object API, but completeness is not
    # claimed, so cleanup stays off.
    assert complete is False
    assert assignments_complete is False
    assert inherited_complete is False
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
    account_usage_by_role, _, _ = (
        cartography.intel.snowflake.account_usage.split_grants(
            SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_ROLES, []
        )
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


@pytest.mark.parametrize("account_grants_complete", [False, True])
@pytest.mark.parametrize("has_inherited", [False, True])
@pytest.mark.usefixtures("isolated_inherited_grants")
def test_incomplete_privileges_do_not_preserve_revoked_role_assignments(
    neo4j_session, account_grants_complete, has_inherited
):
    # Arrange
    _clear_grant_edges(neo4j_session)
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    roles = _ensure_local_neo4j_has_test_roles(neo4j_session)
    _seed_grant_targets(neo4j_session)
    client = build_test_client()
    inherited = {
        "privilege": "REFERENCES",
        "granted_on": "TABLE",
        "name": None,
        "grantee_name": "SAFETY_INSPECTOR",
        "is_inherited": "true",
        "inherited_from": "ACCOUNT",
        "granted_to": "ROLE",
    }
    inherited_rows = [inherited] if has_inherited else []
    parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID}
    client.run_sql.side_effect = [
        SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_ROLES + inherited_rows,
        SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_USERS,
    ]

    # Act
    complete, assignments_complete, inherited_complete = (
        cartography.intel.snowflake.grants.sync(
            neo4j_session, client, roles, set(), [], parameters
        )
    )

    # Assert
    assert (complete, assignments_complete, inherited_complete) == (True, True, True)
    users_before = check_rels(
        neo4j_session, "SnowflakeUser", "name", "SnowflakeRole", "name", "HAS_ROLE"
    )
    hierarchy_before = check_rels(
        neo4j_session, "SnowflakeRole", "name", "SnowflakeRole", "name", "INCLUDES"
    )
    assert users_before
    assert hierarchy_before
    assert check_rels(
        neo4j_session,
        "SnowflakeRole",
        "name",
        "SnowflakeTable",
        "name",
        "HAS_PRIVILEGE",
    )

    # Arrange: revoke assignments and direct privileges while inherited access remains.
    client.run_sql.side_effect = [inherited_rows, []]
    parameters = {**parameters, "UPDATE_TAG": TEST_UPDATE_TAG + 1}

    # Act
    complete, assignments_complete, inherited_complete = (
        cartography.intel.snowflake.grants.sync(
            neo4j_session, client, roles, set(), [], parameters
        )
    )
    cartography.intel.snowflake.grants.cleanup(
        neo4j_session,
        SNOWFLAKE_ACCOUNT_ID,
        parameters["UPDATE_TAG"],
        object_grants_complete=complete and account_grants_complete,
        role_assignments_complete=assignments_complete,
        inherited_grants_complete=inherited_complete,
    )

    # Assert: assignment cleanup is independent of object-grant completeness.
    assert (complete, assignments_complete, inherited_complete) == (True, True, True)
    assert check_nodes(neo4j_session, "SnowflakeUser", ["name"])
    assert check_nodes(neo4j_session, "SnowflakeRole", ["name"])
    assert (
        check_rels(
            neo4j_session, "SnowflakeUser", "name", "SnowflakeRole", "name", "HAS_ROLE"
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session, "SnowflakeRole", "name", "SnowflakeRole", "name", "INCLUDES"
        )
        == set()
    )
    remaining_privileges = check_rels(
        neo4j_session,
        "SnowflakeRole",
        "name",
        "SnowflakeTable",
        "name",
        "HAS_PRIVILEGE",
    )
    expected_privileges = (
        {("SAFETY_INSPECTOR", "REACTOR_READINGS")}
        if not account_grants_complete
        else set()
    )
    assert remaining_privileges == expected_privileges

    # Arrange: ACCOUNT_USAGE revokes inherited access, independently of SHOW GRANTS.
    client.run_sql.side_effect = [[], []]
    parameters = {**parameters, "UPDATE_TAG": TEST_UPDATE_TAG + 2}

    # Act
    complete, assignments_complete, inherited_complete = (
        cartography.intel.snowflake.grants.sync(
            neo4j_session, client, roles, set(), [], parameters
        )
    )
    cartography.intel.snowflake.grants.cleanup(
        neo4j_session,
        SNOWFLAKE_ACCOUNT_ID,
        parameters["UPDATE_TAG"],
        object_grants_complete=complete and account_grants_complete,
        role_assignments_complete=assignments_complete,
        inherited_grants_complete=inherited_complete,
    )

    # Assert
    assert check_nodes(neo4j_session, "SnowflakeInheritedGrant", ["id"]) == set()


@pytest.mark.parametrize("invalid_field", ["inherited_from", "privilege"])
@pytest.mark.usefixtures("isolated_inherited_grants")
def test_malformed_inherited_grant_preserves_state_without_aborting_sync(
    neo4j_session, invalid_field, caplog
):
    # Arrange
    _clear_grant_edges(neo4j_session)
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    roles = _ensure_local_neo4j_has_test_roles(neo4j_session)
    _seed_grant_targets(neo4j_session)
    client = build_test_client()
    inherited = {
        "privilege": "SELECT",
        "granted_on": "TABLE",
        "grantee_name": "SAFETY_INSPECTOR",
        "is_inherited": "true",
        "inherited_from": "ACCOUNT",
        "granted_to": "ROLE",
    }
    params = {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID}
    client.run_sql.side_effect = [
        SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_ROLES + [inherited],
        SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_USERS,
    ]
    cartography.intel.snowflake.grants.sync(
        neo4j_session, client, roles, set(), [], params
    )
    assert check_rels(
        neo4j_session, "SnowflakeUser", "name", "SnowflakeRole", "name", "HAS_ROLE"
    )

    # Arrange: one malformed grant, one new valid grant, and revoked assignments.
    direct = [
        row
        for row in SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_ROLES
        if row["granted_on"] == "DATABASE"
    ]
    client.run_sql.side_effect = [
        direct
        + [{**inherited, invalid_field: None}, {**inherited, "granted_on": "VIEW"}],
        [],
    ]
    params = {**params, "UPDATE_TAG": TEST_UPDATE_TAG + 1}

    # Act
    complete, assignments, inherited_complete = cartography.intel.snowflake.grants.sync(
        neo4j_session, client, roles, set(), [], params
    )
    cartography.intel.snowflake.grants.cleanup(
        neo4j_session,
        SNOWFLAKE_ACCOUNT_ID,
        params["UPDATE_TAG"],
        object_grants_complete=complete,
        role_assignments_complete=assignments,
        inherited_grants_complete=inherited_complete,
    )

    # Assert: preserve only inherited state; direct grants and assignments still revoke.
    assert (complete, assignments, inherited_complete) == (True, True, False)
    assert "Skipping malformed Snowflake inherited grant" in caplog.text
    assert "SAFETY_INSPECTOR" in caplog.text
    assert check_nodes(
        neo4j_session, "SnowflakeInheritedGrant", ["object_type", "lastupdated"]
    ) == {("TABLE", TEST_UPDATE_TAG), ("VIEW", TEST_UPDATE_TAG + 1)}
    assert (
        check_rels(
            neo4j_session, "SnowflakeUser", "name", "SnowflakeRole", "name", "HAS_ROLE"
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session, "SnowflakeRole", "name", "SnowflakeRole", "name", "INCLUDES"
        )
        == set()
    )
    assert (
        neo4j_session.run(
            "MATCH (:SnowflakeRole)-[r:HAS_PRIVILEGE]->(:SnowflakeDatabase) "
            "RETURN r.lastupdated AS tag"
        ).single()["tag"]
        == params["UPDATE_TAG"]
    )
    assert (
        check_rels(
            neo4j_session,
            "SnowflakeRole",
            "name",
            "SnowflakeTable",
            "name",
            "HAS_PRIVILEGE",
        )
        == set()
    )


@pytest.mark.parametrize("scope", ["ACCOUNT", "DATABASE", "SCHEMA"])
@pytest.mark.usefixtures("isolated_inherited_grants")
def test_inherited_grants_refresh_and_revoke_without_preserving_direct_grants(
    neo4j_session, scope
):
    # Arrange
    _clear_grant_edges(neo4j_session)
    _ensure_local_neo4j_has_test_account(neo4j_session)
    roles = _ensure_local_neo4j_has_test_roles(neo4j_session)
    _seed_grant_targets(neo4j_session)
    schema_id = f"{SNOWFLAKE_ACCOUNT_ID}/schema/SPRINGFIELD_DB.NUCLEAR_PLANT"
    neo4j_session.run(
        "MERGE (:SnowflakeSchema:SnowflakeSecurable {id: $id, name: 'NUCLEAR_PLANT'})",
        id=schema_id,
    )
    direct = [
        row
        for row in SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_ROLES
        if row["granted_on"] == "TABLE"
    ]
    inherited = {
        "granted_to": "ROLE",
        "grantee_name": "SAFETY_INSPECTOR",
        "granted_on": "TABLE",
        "privilege": "SELECT",
        "is_inherited": True,
        "inherited_from": scope,
        "inherited_from_database": "SPRINGFIELD_DB",
        "inherited_from_schema": "NUCLEAR_PLANT",
    }
    view_grant = {**inherited, "granted_on": "VIEW"}
    client = build_test_client()
    params = {"ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID, "UPDATE_TAG": TEST_UPDATE_TAG}
    client.run_sql.side_effect = [direct + [inherited, view_grant], []]

    # Act
    complete, assignments, inherited_complete = cartography.intel.snowflake.grants.sync(
        neo4j_session, client, roles, set(), [], params
    )

    # Assert
    assert complete and assignments
    assert check_nodes(
        neo4j_session, "SnowflakeInheritedGrant", ["object_type", "privilege"]
    ) == {("TABLE", "SELECT"), ("VIEW", "SELECT")}
    assert check_rels(
        neo4j_session,
        "SnowflakeRole",
        "name",
        "SnowflakeInheritedGrant",
        "object_type",
        "HAS_INHERITED_GRANT",
    ) == {("SAFETY_INSPECTOR", "TABLE"), ("SAFETY_INSPECTOR", "VIEW")}
    target_id = {
        "ACCOUNT": SNOWFLAKE_ACCOUNT_ID,
        "DATABASE": f"{SNOWFLAKE_ACCOUNT_ID}/database/SPRINGFIELD_DB",
        "SCHEMA": schema_id,
    }[scope]
    linked = neo4j_session.run(
        "MATCH (g:SnowflakeInheritedGrant)-[:APPLIES_IN]->(c) RETURN g.object_type AS kind, c.id AS container"
    ).data()
    assert {(r["kind"], r["container"]) for r in linked} == {
        ("TABLE", target_id),
        ("VIEW", target_id),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeRole",
        "name",
        "SnowflakeTable",
        "name",
        "HAS_PRIVILEGE",
    ) == {("SAFETY_INSPECTOR", "REACTOR_READINGS")}

    # Arrange: revoke the direct grant while both inherited grants remain.
    client.run_sql.side_effect = [[inherited, view_grant], []]
    params = {**params, "UPDATE_TAG": TEST_UPDATE_TAG + 1}

    # Act
    complete, assignments, inherited_complete = cartography.intel.snowflake.grants.sync(
        neo4j_session, client, roles, set(), [], params
    )
    cartography.intel.snowflake.grants.cleanup(
        neo4j_session,
        SNOWFLAKE_ACCOUNT_ID,
        params["UPDATE_TAG"],
        object_grants_complete=complete,
        role_assignments_complete=assignments,
        inherited_grants_complete=inherited_complete,
    )

    # Assert
    assert (
        check_rels(
            neo4j_session,
            "SnowflakeRole",
            "name",
            "SnowflakeTable",
            "name",
            "HAS_PRIVILEGE",
        )
        == set()
    )
    assert check_nodes(neo4j_session, "SnowflakeInheritedGrant", ["object_type"]) == {
        ("TABLE",),
        ("VIEW",),
    }

    # Arrange: revoke one inherited object type, preserving the other.
    client.run_sql.side_effect = [[view_grant], []]
    params = {**params, "UPDATE_TAG": TEST_UPDATE_TAG + 2}

    # Act
    complete, assignments, inherited_complete = cartography.intel.snowflake.grants.sync(
        neo4j_session, client, roles, set(), [], params
    )
    cartography.intel.snowflake.grants.cleanup(
        neo4j_session,
        SNOWFLAKE_ACCOUNT_ID,
        params["UPDATE_TAG"],
        object_grants_complete=complete,
        role_assignments_complete=assignments,
        inherited_grants_complete=inherited_complete,
    )

    # Assert
    assert check_nodes(
        neo4j_session, "SnowflakeInheritedGrant", ["object_type", "lastupdated"]
    ) == {("VIEW", TEST_UPDATE_TAG + 2)}


@pytest.mark.usefixtures("isolated_inherited_grants")
def test_inherited_grant_cleanup_is_account_scoped(neo4j_session):
    # Arrange
    accounts = ["EXAMPLE.FIRST", "EXAMPLE.SECOND"]
    row = {
        "granted_to": "ROLE",
        "grantee_name": "READER",
        "granted_on": "TABLE",
        "privilege": "SELECT",
        "inherited_from": "ACCOUNT",
    }
    for account in accounts:
        neo4j_session.run(
            "MERGE (:SnowflakeAccount:SnowflakeSecurable {id: $id})", id=account
        )
        load_grants(neo4j_session, [row], account, TEST_UPDATE_TAG)

    # Act
    cleanup(neo4j_session, accounts[0], TEST_UPDATE_TAG + 1)

    # Assert
    query = "MATCH (a:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeInheritedGrant) WHERE a.id IN $ids RETURN a.id AS id"
    assert {r["id"] for r in neo4j_session.run(query, ids=accounts)} == {accounts[1]}

    # Arrange
    load_grants(neo4j_session, [row], accounts[0], TEST_UPDATE_TAG + 2)

    # Act
    cleanup(neo4j_session, accounts[1], TEST_UPDATE_TAG + 2)

    # Assert
    assert {r["id"] for r in neo4j_session.run(query, ids=accounts)} == {accounts[0]}
