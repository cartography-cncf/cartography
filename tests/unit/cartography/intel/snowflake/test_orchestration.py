"""Neo4j-free tests for the Snowflake module entry point.

These cover credential validation, input parsing, the cleanup gate and the
cleanup ordering constants. The Neo4j-backed entry-point tests live in
tests/integration/cartography/intel/snowflake/test_orchestration.py.
"""

import importlib
import pkgutil
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.snowflake
from cartography.config import Config
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID

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


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        # Supplying both is ambiguous, so it must not silently pick one.
        pytest.param(
            {"snowflake_private_key": "-----BEGIN PRIVATE KEY-----"},
            "ambiguously configured",
            id="both_credentials",
        ),
        # This is the shape of a typo'd env-var name, which must fail loudly
        # rather than fall through to "not configured".
        pytest.param(
            {
                "snowflake_pat": None,
                "snowflake_private_key": None,
                "snowflake_private_key_passphrase": "hunter2",
            },
            "partially configured",
            id="passphrase_without_key",
        ),
        pytest.param(
            {"snowflake_user": None},
            "without --snowflake-user",
            id="missing_user",
        ),
    ],
)
def test_build_client_rejects_misconfigured_credentials(overrides, match):
    # Arrange
    config = _config(**overrides)

    # Act + Assert
    with pytest.raises(ValueError, match=match):
        cartography.intel.snowflake._build_client(config)


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


def test_cleanup_skips_surfaces_that_could_not_be_read():
    # Arrange: two modules, one of which this run failed to read in full.
    neo4j_session = MagicMock()
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


def test_cleanup_order_covers_every_synced_module():
    # Arrange: a module missing from the cleanup order would leak stale nodes
    # forever, and one listed twice would run redundant jobs.
    order = cartography.intel.snowflake._CLEANUP_ORDER
    names = [module.__name__.rsplit(".", 1)[-1] for module in order]

    # Assert no duplicates.
    assert len(names) == len(set(names)), f"duplicated in cleanup order: {names}"

    # Assert every Snowflake module that defines a cleanup() is in the order. Grant
    # edges are the exception: grants.cleanup() removes them after the grant syncs,
    # gated on their completeness, outside the module order.
    grant_modules = {"grants", "account_grants", "inherited_grants"}
    expected = set()
    for module_info in pkgutil.iter_modules(cartography.intel.snowflake.__path__):
        module = importlib.import_module(
            f"cartography.intel.snowflake.{module_info.name}"
        )
        if callable(getattr(module, "cleanup", None)):
            expected.add(module_info.name)
    expected -= grant_modules
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
