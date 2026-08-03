"""End-to-end tests for the Snowflake module entry point.

The per-domain tests exercise each sync in isolation, which leaves the entry point
itself untested. Three of its behaviours are where the module can do real damage,
so they are covered here:

- credential validation, which must fail loudly on a half-configured credential
  rather than silently skipping the module;
- the ordering of the fan-out, which is what lets edges resolve on the first pass;
- the cleanup gate, which must NOT delete a surface this run could not read.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

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


def test_both_credentials_together_is_an_error():
    # Arrange: supplying both is ambiguous, so it must not silently pick one.
    config = _config(snowflake_private_key="-----BEGIN PRIVATE KEY-----")

    # Act + Assert
    with pytest.raises(ValueError, match="ambiguously configured"):
        cartography.intel.snowflake._build_client(config)


def test_a_passphrase_without_a_private_key_is_an_error():
    # Arrange: this is the shape of a typo'd env-var name, which must fail loudly
    # rather than fall through to "not configured".
    config = _config(
        snowflake_pat=None,
        snowflake_private_key=None,
        snowflake_private_key_passphrase="hunter2",
    )

    # Act + Assert
    with pytest.raises(ValueError, match="partially configured"):
        cartography.intel.snowflake._build_client(config)


def test_a_missing_user_is_an_error():
    # Act + Assert
    with pytest.raises(ValueError, match="without --snowflake-user"):
        cartography.intel.snowflake._build_client(_config(snowflake_user=None))


def test_account_id_is_normalized_from_the_url_form():
    # Arrange: operators paste either separator; the graph must key on one form.
    # Act
    client = cartography.intel.snowflake._build_client(
        _config(snowflake_account="springfield-nuclear")
    )

    # Assert
    assert client.account_id == SNOWFLAKE_ACCOUNT_ID


def test_parse_databases_normalizes_and_drops_blanks():
    # Act
    parsed = cartography.intel.snowflake._parse_databases(" springfield , ,monorail ")

    # Assert: the operator's casing is preserved. Snowflake folds an unquoted
    # identifier to uppercase but keeps the case of a quoted one, so upper-casing here
    # would drop a database created as "springfield"; the membership test in
    # databases._skip_walk_reason is case-insensitive instead.
    assert parsed == {"springfield", "monorail"}
    assert cartography.intel.snowflake._parse_databases(None) is None
    assert cartography.intel.snowflake._parse_databases("") is None
    assert cartography.intel.snowflake._parse_databases("  ,  ") is None


def test_cleanup_skips_surfaces_that_could_not_be_read(neo4j_session):
    # Arrange: two modules, one of which this run failed to read in full.
    read_module = MagicMock()
    read_module.__name__ = "cartography.intel.snowflake.roles"
    unread_module = MagicMock()
    unread_module.__name__ = "cartography.intel.snowflake.tables"

    with patch.object(
        cartography.intel.snowflake,
        "_CLEANUP_ORDER",
        (read_module, unread_module),
    ):
        # Act
        cartography.intel.snowflake._cleanup(
            neo4j_session,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
            incomplete={"tables"},
        )

    # Assert: the surface that was read gets cleaned, and the one that was not is
    # left alone. Cleaning it would delete inventory Cartography simply could not
    # re-observe this run, which is worse than keeping it stale.
    read_module.cleanup.assert_called_once()
    unread_module.cleanup.assert_not_called()


def test_an_unreadable_database_protects_every_schema_scoped_surface():
    """A truncated schema list must suppress cleanup for everything below it.

    When one database cannot be listed, its schemas never reach the object-level
    syncs. Those syncs walk exactly the schemas they were handed, so they report
    complete=True in good faith while holding none of that database's objects. Their
    cleanup is account-scoped, so without this propagation it would delete the
    unread database's tables, views and tasks as though they had been dropped.
    """
    # Arrange
    surfaces = cartography.intel.snowflake._SCHEMA_SCOPED_SURFACES

    # Assert the set actually spans the surfaces that walk the schema list, rather
    # than being a stale hand-written list.
    assert {"tables", "views", "tasks", "stages", "secrets", "streams"} <= surfaces
    assert {"network_rules", "database_roles", "schemas"} <= surfaces
    # Account-level surfaces do not walk schemas, so they are deliberately absent.
    assert "warehouses" not in surfaces
    assert "roles" not in surfaces
    assert "users" not in surfaces

    # Act + Assert the gate itself.
    assert cartography.intel.snowflake.databases_and_schemas_complete(set()) is True
    assert (
        cartography.intel.snowflake.databases_and_schemas_complete({"warehouses"})
        is True
    )
    assert (
        cartography.intel.snowflake.databases_and_schemas_complete({"schemas"}) is False
    )
    assert (
        cartography.intel.snowflake.databases_and_schemas_complete({"databases"})
        is False
    )


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


def test_cleanup_order_covers_every_synced_module():
    # Arrange: a module missing from the cleanup order would leak stale nodes
    # forever, and one listed twice would run redundant jobs.
    order = cartography.intel.snowflake._CLEANUP_ORDER
    names = [module.__name__.rsplit(".", 1)[-1] for module in order]

    # Assert no duplicates.
    assert len(names) == len(set(names)), f"duplicated in cleanup order: {names}"

    # Assert every module that participates in the fan-out is cleaned up.
    expected = {
        name
        for group in (
            cartography.intel.snowflake._SCHEMA_LEVEL_MODULES,
            cartography.intel.snowflake._WORKLOAD_MODULES,
            cartography.intel.snowflake._INTEGRATION_MODULES,
        )
        for name in (module.__name__.rsplit(".", 1)[-1] for module in group)
    }
    assert expected <= set(names), f"not cleaned up: {sorted(expected - set(names))}"


def test_containment_parents_are_cleaned_after_their_children():
    # Arrange: cleanup deletes nodes, so a parent must not be deleted while a child
    # still hangs off it. Databases contain schemas, which contain tables.
    names = [
        module.__name__.rsplit(".", 1)[-1]
        for module in cartography.intel.snowflake._CLEANUP_ORDER
    ]

    # Assert
    assert names.index("tables") < names.index("schemas")
    assert names.index("schemas") < names.index("databases")
    assert names.index("database_roles") < names.index("databases")
    # Roles and users are the target of grant edges, so they go late.
    assert names.index("access_tokens") < names.index("users")
    assert names.index("users") < names.index("roles")
    # The account tenant is last: everything else hangs off it.
    assert names[-1] == "account"
