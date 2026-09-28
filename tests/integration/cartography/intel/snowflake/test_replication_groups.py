from unittest.mock import patch

import cartography.intel.snowflake.replication_groups
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.replication_groups import SNOWFLAKE_FAILOVER_GROUPS
from tests.data.snowflake.replication_groups import SNOWFLAKE_REPLICATION_GROUPS
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def _seed_replicated_database(neo4j_session) -> None:
    neo4j_session.run(
        """
        MERGE (d:SnowflakeDatabase:SnowflakeSecurable {id: $database_id})
          SET d.name = 'SPRINGFIELD', d.lastupdated = $update_tag
        """,
        database_id=sf_id(SNOWFLAKE_ACCOUNT_ID, "database", sf_fqn("SPRINGFIELD")),
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.snowflake.replication_groups,
    "get_failover_groups",
    return_value=SNOWFLAKE_FAILOVER_GROUPS,
)
@patch.object(
    cartography.intel.snowflake.replication_groups,
    "get_replication_groups",
    return_value=SNOWFLAKE_REPLICATION_GROUPS,
)
def test_sync_snowflake_replication_groups(
    mock_replication, mock_failover, neo4j_session
):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _seed_replicated_database(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.replication_groups.sync(
        neo4j_session, client, common_job_parameters
    )

    # Assert
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeReplicationGroup",
        ["name", "is_primary", "replication_schedule"],
    ) == {("REACTOR_REPLICA", True, "10 MINUTE")}
    # Failover groups are a distinct label because promotion is a distinct capability.
    assert check_nodes(
        neo4j_session,
        "SnowflakeFailoverGroup",
        ["name", "is_primary", "secondary_state"],
    ) == {("PLANT_FAILOVER", False, "STARTED")}

    # A comma-separated SHOW column has to arrive as a list, since that is what makes
    # "this group replicates identities" queryable.
    object_types = neo4j_session.run(
        """
        MATCH (group:SnowflakeFailoverGroup {name: 'PLANT_FAILOVER'})
        RETURN group.object_types AS object_types
        """,
    ).single()["object_types"]
    assert object_types == ["DATABASES", "USERS", "ROLES"]

    assert check_rels(
        neo4j_session,
        "SnowflakeReplicationGroup",
        "name",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("REACTOR_REPLICA", SNOWFLAKE_ACCOUNT_ID)}

    # Only the sibling account inside the organization has a node, so the account
    # outside it produces no edge while staying in the raw list.
    assert check_rels(
        neo4j_session,
        "SnowflakeReplicationGroup",
        "name",
        "SnowflakeAccount",
        "id",
        "REPLICATES_TO",
        rel_direction_right=True,
    ) == {("REACTOR_REPLICA", "SPRINGFIELD.KWIKEMART")}
    assert check_rels(
        neo4j_session,
        "SnowflakeFailoverGroup",
        "name",
        "SnowflakeAccount",
        "id",
        "REPLICATES_TO",
        rel_direction_right=True,
    ) == {("PLANT_FAILOVER", "SPRINGFIELD.KWIKEMART")}

    assert check_rels(
        neo4j_session,
        "SnowflakeReplicationGroup",
        "name",
        "SnowflakeDatabase",
        "name",
        "REPLICATES",
        rel_direction_right=True,
    ) == {("REACTOR_REPLICA", "SPRINGFIELD")}


@patch.object(
    cartography.intel.snowflake.replication_groups,
    "get_failover_groups",
    return_value=None,
)
@patch.object(
    cartography.intel.snowflake.replication_groups,
    "get_replication_groups",
    return_value=SNOWFLAKE_REPLICATION_GROUPS,
)
def test_sync_reports_incomplete_when_failover_groups_are_unavailable(
    mock_replication, mock_failover, neo4j_session
):
    """Failover groups need Business Critical, so their absence is expected.

    The replication groups that did answer are still loaded, but the module reports
    incomplete so cleanup does not delete the failover groups a higher-edition run
    collected.
    """
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run("MATCH (group:SnowflakeFailoverGroup) DETACH DELETE group")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.replication_groups.sync(
        neo4j_session, client, common_job_parameters
    )

    # Assert
    assert complete is False
    assert check_nodes(neo4j_session, "SnowflakeFailoverGroup", ["id"]) == set()
    assert check_nodes(neo4j_session, "SnowflakeReplicationGroup", ["name"]) == {
        ("REACTOR_REPLICA",),
    }
