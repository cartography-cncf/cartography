import pytest

from cartography.intel.snowflake.inherited_grants import transform
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id


@pytest.mark.parametrize(
    "scope,parts",
    [
        ("ACCOUNT", []),
        ("DATABASE", ["mixed.Db"]),
        ("SCHEMA", ["mixed.Db", "lower-schema"]),
    ],
)
def test_container_ids_and_object_types_are_preserved(scope, parts):
    # Arrange
    row = {
        "granted_to": "ROLE",
        "grantee_name": "READER",
        "granted_on": "TABLE",
        "privilege": "SELECT",
        "inherited_from": scope,
        "inherited_from_database": "mixed.Db",
        "inherited_from_schema": "lower-schema",
    }

    # Act
    table, view = transform([row, {**row, "granted_on": "VIEW"}], "EXAMPLE.ACCOUNT")

    # Assert
    assert table["container_id"] == (
        sf_id("EXAMPLE.ACCOUNT", scope.lower(), sf_fqn(*parts))
        if parts
        else "EXAMPLE.ACCOUNT"
    )
    assert table["id"] != view["id"]
    assert table["privilege"] == view["privilege"] == "SELECT"
    assert table["object_type"] == "TABLE"
    assert view["object_type"] == "VIEW"
    assert table["principal_id"] == sf_id("EXAMPLE.ACCOUNT", "role", "READER")


@pytest.mark.parametrize("scope", [None, "UNKNOWN", "DATABASE", "SCHEMA"])
def test_missing_container_metadata_is_skipped_and_warned(scope, caplog):
    # Arrange
    row = {
        "granted_to": "ROLE",
        "grantee_name": "READER",
        "granted_on": "TABLE",
        "privilege": "SELECT",
        "inherited_from": scope,
    }

    # Act and assert
    assert transform([row], "EXAMPLE.ACCOUNT") == []
    assert "container scope" in caplog.text
    assert "READER" in caplog.text and "SELECT" in caplog.text


@pytest.mark.parametrize(
    "grantee_type,name,principal_suffix",
    [
        ("ACCOUNT_ROLE", "READER", "role/READER"),
        ("DATABASE_ROLE", "example.reader", 'database_role/"example"."reader"'),
        ("USER", "collector", "user/collector"),
        ("APPLICATION_ROLE", "EXAMPLE.APP_READER", None),
    ],
)
def test_grantee_identity_is_preserved(grantee_type, name, principal_suffix):
    # Arrange
    row = {
        "granted_to": grantee_type,
        "grantee_name": name,
        "granted_on": "TABLE",
        "privilege": "SELECT",
        "inherited_from": "ACCOUNT",
    }

    # Act
    grant = transform([row], "EXAMPLE.ACCOUNT")[0]

    # Assert
    assert grant["principal_id"] == (
        f"EXAMPLE.ACCOUNT/{principal_suffix}" if principal_suffix else None
    )
    assert grant["grantee_name"] == name
    assert grant["grantee_type"] == grantee_type.replace("_", " ")
