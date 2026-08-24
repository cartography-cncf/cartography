from unittest.mock import patch

import cartography.intel.snowflake.account_grants
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.account_grants import SNOWFLAKE_ACCOUNT_GRANTS
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_grants import (
    _ensure_local_neo4j_has_test_roles,
)
from tests.integration.util import check_rels


@patch.object(
    cartography.intel.snowflake.account_grants,
    "get",
    return_value=SNOWFLAKE_ACCOUNT_GRANTS,
)
def test_sync_snowflake_account_grants(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_roles(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.account_grants.sync(
        neo4j_session, client, common_job_parameters
    )

    # Assert
    assert complete is True
    # The account-level privileges land on the account node itself, keyed on the
    # account identifier rather than on the locator the statement reports.
    assert check_rels(
        neo4j_session,
        "SnowflakeRole",
        "name",
        "SnowflakeAccount",
        "id",
        "HAS_PRIVILEGE",
        rel_direction_right=True,
    ) == {
        ("SAFETY_INSPECTOR", SNOWFLAKE_ACCOUNT_ID),
        ("SYSADMIN", SNOWFLAKE_ACCOUNT_ID),
    }

    # The two privileges granted to one role collapse into a single edge carrying
    # both, and WITH GRANT OPTION on either makes the whole grant onward-grantable.
    edges = {
        row["role"]: (row["privileges"], row["grant_option"])
        for row in neo4j_session.run(
            """
            MATCH (role:SnowflakeRole)-[r:HAS_PRIVILEGE]->(:SnowflakeAccount)
            RETURN role.name AS role, r.privileges AS privileges,
                   r.grant_option AS grant_option
            """,
        )
    }
    assert edges == {
        "SAFETY_INSPECTOR": (["CREATE USER", "MANAGE GRANTS"], True),
        "SYSADMIN": (["CREATE DATABASE"], False),
    }


@patch.object(cartography.intel.snowflake.account_grants, "get", return_value=None)
def test_sync_reports_incomplete_when_account_grants_cannot_be_read(
    mock_get, neo4j_session
):
    """Losing the listing must not delete the account grants of an earlier run."""
    # Arrange: start from a clean slate, then seed the edge an earlier successful run
    # would have left behind. Without a pre-existing edge there is nothing to preserve
    # and the assertion below would hold trivially.
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_roles(neo4j_session)
    neo4j_session.run(
        "MATCH (:SnowflakeRole)-[r:HAS_PRIVILEGE]->(:SnowflakeAccount) DELETE r",
    )
    neo4j_session.run(
        """
        MATCH (role:SnowflakeRole {name: 'SYSADMIN'})
        MATCH (account:SnowflakeAccount {id: $account_id})
        MERGE (role)-[r:HAS_PRIVILEGE]->(account)
          SET r.privileges = ['CREATE DATABASE'], r.lastupdated = $old_tag
        """,
        account_id=SNOWFLAKE_ACCOUNT_ID,
        old_tag=TEST_UPDATE_TAG - 1,
    )
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.account_grants.sync(
        neo4j_session, client, common_job_parameters
    )

    # Assert: the sync reports incomplete, which is what makes the caller skip grant
    # cleanup, and the earlier run's edge is still there rather than overwritten or
    # deleted.
    assert complete is False
    assert check_rels(
        neo4j_session,
        "SnowflakeRole",
        "name",
        "SnowflakeAccount",
        "id",
        "HAS_PRIVILEGE",
        rel_direction_right=True,
    ) == {("SYSADMIN", SNOWFLAKE_ACCOUNT_ID)}
