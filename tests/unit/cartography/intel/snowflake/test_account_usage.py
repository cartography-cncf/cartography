import pytest

from cartography.intel.snowflake.account_usage import split_grants


@pytest.mark.parametrize("inherited_from", ["ACCOUNT", "DATABASE", "SCHEMA"])
@pytest.mark.parametrize("name", [None, "", "EXAMPLE_TABLE"])
def test_inherited_grants_are_not_loaded_as_object_grants(inherited_from, name):
    # Arrange
    ordinary = {
        "privilege": "REFERENCES",
        "granted_on": "TABLE",
        "name": "EXAMPLE_TABLE",
        "table_catalog": "EXAMPLE_DB",
        "table_schema": "EXAMPLE_SCHEMA",
        "grantee_name": "INVENTORY_READER",
        "is_inherited": "false",
    }
    inherited = {
        **ordinary,
        "name": name,
        "is_inherited": "true",
        "inherited_from": inherited_from,
        "inherited_from_database": (
            "EXAMPLE_DB" if inherited_from != "ACCOUNT" else None
        ),
        "inherited_from_schema": (
            "EXAMPLE_SCHEMA" if inherited_from == "SCHEMA" else None
        ),
    }

    # Act
    grants, assignments = split_grants([ordinary, inherited], [])

    # Assert
    assert list(grants) == ["INVENTORY_READER"]
    assert len(grants["INVENTORY_READER"]) == 1
    assert grants["INVENTORY_READER"][0]["securable"]["name"] == "EXAMPLE_TABLE"
    assert grants["INVENTORY_READER"][0]["privileges"] == ["REFERENCES"]
    assert assignments == {}
