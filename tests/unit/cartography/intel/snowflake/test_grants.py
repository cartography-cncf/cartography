import cartography.intel.snowflake.account_usage
import cartography.intel.snowflake.grants
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.roles import SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_ROLES
from tests.data.snowflake.roles import SNOWFLAKE_ROLE_GRANTS


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
