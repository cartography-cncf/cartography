"""End-to-end tests for the Snowflake module entry point.

The per-domain tests exercise each sync in isolation, which leaves the entry point
itself untested. Three of its behaviours are where the module can do real damage,
so they are covered here:

- credential validation, which must fail loudly on a half-configured credential
  rather than silently skipping the module;
- the ordering of the fan-out, which is what lets edges resolve on the first pass;
- the cleanup gate, which must NOT delete a surface this run could not read.

The checks that need no graph live in
tests/unit/cartography/intel/snowflake/test_orchestration.py.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.snowflake
import cartography.intel.snowflake.account
from cartography.config import Config
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 987660000


def _config(**overrides):
    defaults = {
        "neo4j_uri": "bolt://localhost:7687",
        "update_tag": TEST_UPDATE_TAG,
        "snowflake_account": "SPRINGFIELD-NUCLEAR",
        "snowflake_user": "CARTOGRAPHY_SVC",
        "snowflake_pat": "fake-pat",
    }
    return Config(**{**defaults, **overrides})


def test_module_is_skipped_when_unconfigured(neo4j_session):
    # Arrange: no account configured at all.
    # Act
    cartography.intel.snowflake.start_snowflake_ingestion(
        neo4j_session, _config(snowflake_account=None)
    )

    # Assert: nothing is written and nothing raises.
    assert check_nodes(neo4j_session, "SnowflakeAccount", ["id"]) == set()


def test_module_is_skipped_when_no_credential_is_supplied(neo4j_session):
    # Arrange: an account but neither a token nor a key.
    # Act
    cartography.intel.snowflake.start_snowflake_ingestion(
        neo4j_session, _config(snowflake_pat=None)
    )

    # Assert
    assert check_nodes(neo4j_session, "SnowflakeAccount", ["id"]) == set()


def test_an_unreadable_database_does_not_delete_its_tables(neo4j_session):
    """The concrete data loss the propagation prevents.

    A table belonging to a database that could not be listed this run must survive
    cleanup. Table cleanup is scoped to the account, so it would otherwise match a
    table whose whole database was simply unreadable and delete it.
    """
    # Arrange: a table from a previous run, in a database this run cannot list.
    _ensure_local_neo4j_has_test_account(neo4j_session)
    table_id = f"{SNOWFLAKE_ACCOUNT_ID}/table/LOCKED_DB.SECRETS.PAYROLL"
    neo4j_session.run(
        """
        MATCH (a:SnowflakeAccount {id: $account_id})
        MERGE (t:SnowflakeTable {id: $table_id})
          SET t.name = 'PAYROLL', t.lastupdated = $old_tag
        MERGE (a)-[r:RESOURCE]->(t)
          SET r.lastupdated = $old_tag
        """,
        account_id=SNOWFLAKE_ACCOUNT_ID,
        table_id=table_id,
        old_tag=TEST_UPDATE_TAG - 1,
    )

    # Act: cleanup runs with the schema walk reported incomplete, which is what the
    # entry point does after propagating the failure to every schema-scoped surface.
    cartography.intel.snowflake._cleanup(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        incomplete=set(cartography.intel.snowflake._SCHEMA_SCOPED_SURFACES),
    )

    # Assert the table survived.
    assert check_nodes(neo4j_session, "SnowflakeTable", ["id"]) == {(table_id,)}


def test_a_complete_run_still_deletes_stale_tables(neo4j_session):
    """The counterpart: when the walk was complete, stale nodes must still go.

    Skipping cleanup on incompleteness is only safe because a complete run still
    prunes. Without this, the module would accumulate deleted objects forever.
    """
    # Arrange: a stale table from a previous run, and a complete walk this run.
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run(
        """
        MATCH (a:SnowflakeAccount {id: $account_id})
        MERGE (t:SnowflakeTable {id: $table_id})
          SET t.name = 'DROPPED_TABLE', t.lastupdated = $old_tag
        MERGE (a)-[r:RESOURCE]->(t)
          SET r.lastupdated = $old_tag
        """,
        account_id=SNOWFLAKE_ACCOUNT_ID,
        table_id=f"{SNOWFLAKE_ACCOUNT_ID}/table/SPRINGFIELD.PUBLIC.DROPPED_TABLE",
        old_tag=TEST_UPDATE_TAG - 1,
    )

    # Act
    cartography.intel.snowflake._cleanup(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        incomplete=set(),
    )

    # Assert the stale table is gone.
    assert check_nodes(neo4j_session, "SnowflakeTable", ["name"]) == set()


def test_unreadable_managed_accounts_do_not_delete_previously_ingested_ones(
    neo4j_session,
):
    """An unauthorized managed-account listing must not erase reader accounts.

    ``get_managed_accounts`` turns a 403 into None, which becomes an empty list once
    transformed. That is indistinguishable from "this account has no reader
    accounts", so the sync has to report the failure or the account cleanup job
    deletes every reader account previously collected.
    """
    # Arrange: a reader account already in the graph from an earlier run.
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run(
        """
        MATCH (a:SnowflakeAccount {id: $account_id})
        MERGE (m:SnowflakeManagedAccount {id: $managed_id})
          SET m.name = 'SHELBYVILLE_READER', m.lastupdated = $old_tag
        MERGE (a)-[r:RESOURCE]->(m)
          SET r.lastupdated = $old_tag
        """,
        account_id=SNOWFLAKE_ACCOUNT_ID,
        managed_id=f"{SNOWFLAKE_ACCOUNT_ID}/managed_account/SHELBYVILLE_READER",
        old_tag=TEST_UPDATE_TAG - 1,
    )
    client = MagicMock()
    client.account_id = SNOWFLAKE_ACCOUNT_ID

    # Act: the listing is unauthorized this run.
    with (
        patch.object(
            cartography.intel.snowflake.account,
            "get_organization_accounts",
            return_value=None,
        ),
        patch.object(
            cartography.intel.snowflake.account,
            "get_managed_accounts",
            return_value=None,
        ),
    ):
        complete = cartography.intel.snowflake.account.sync(
            neo4j_session,
            client,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )

    # Assert the failure is reported, which is what gates the cleanup.
    assert complete is False

    # Act: run the cleanup the way the entry point would, with the failure recorded.
    cartography.intel.snowflake._cleanup(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        incomplete={"account"},
    )

    # Assert the stale reader account survived rather than being deleted.
    assert check_nodes(neo4j_session, "SnowflakeManagedAccount", ["name"]) == {
        ("SHELBYVILLE_READER",)
    }
