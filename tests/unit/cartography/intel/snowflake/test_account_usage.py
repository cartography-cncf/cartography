import pytest

from cartography.intel.snowflake.account_usage import get_grants_to_roles
from cartography.intel.snowflake.account_usage import split_grants
from cartography.intel.snowflake.util import SnowflakeSqlError


@pytest.mark.parametrize("ordinary_flag", [None, "false", False])
@pytest.mark.parametrize("inherited_from", ["ACCOUNT", "DATABASE", "SCHEMA"])
@pytest.mark.parametrize("name", [None, "", "EXAMPLE_TABLE"])
def test_inherited_grants_are_not_loaded_as_object_grants(
    inherited_from, name, ordinary_flag
):
    # Arrange
    ordinary = {
        "privilege": "REFERENCES",
        "granted_on": "TABLE",
        "name": "EXAMPLE_TABLE",
        "table_catalog": "EXAMPLE_DB",
        "table_schema": "EXAMPLE_SCHEMA",
        "grantee_name": "INVENTORY_READER",
    }
    if ordinary_flag is not None:
        ordinary["is_inherited"] = ordinary_flag
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
    grants, assignments, inherited_count = split_grants([ordinary, inherited], [])

    # Assert
    assert list(grants) == ["INVENTORY_READER"]
    assert len(grants["INVENTORY_READER"]) == 1
    assert grants["INVENTORY_READER"][0]["securable"]["name"] == "EXAMPLE_TABLE"
    assert grants["INVENTORY_READER"][0]["privileges"] == ["REFERENCES"]
    assert assignments == {}
    assert inherited_count == 1


@pytest.mark.parametrize("has_inherited", [False, True])
def test_grant_query_projects_only_supported_columns(mocker, has_inherited):
    # Arrange
    client = mocker.Mock()
    columns = [{"column_name": "PRIVILEGE"}, {"column_name": "DELETED_ON"}]
    if has_inherited:
        columns.append({"column_name": "IS_INHERITED"})
    rows = [{"privilege": "REFERENCES"}]
    client.run_sql.side_effect = [columns, rows]

    # Act
    result = get_grants_to_roles(client)

    # Assert
    assert result == rows
    assert client.run_sql.call_count == 2
    assert client.run_sql.call_args_list[0].args == (
        "SHOW COLUMNS IN VIEW snowflake.account_usage.grants_to_roles",
    )
    statement = client.run_sql.call_args.args[0].lower()
    projection = statement.split("from", 1)[0]
    projected_columns = {
        column.strip()
        for column in projection.strip().removeprefix("select").split(",")
    }
    expected_columns = {
        "privilege",
        "granted_on",
        "name",
        "table_catalog",
        "table_schema",
        "granted_to",
        "grantee_name",
        "grant_option",
        "granted_by",
        "created_on",
    }
    if has_inherited:
        expected_columns.add("is_inherited")
    assert projected_columns == expected_columns
    assert "where deleted_on is null" in statement


@pytest.mark.parametrize(
    "error", [None, "Insufficient privileges", "Unexpected SQL failure"]
)
def test_grant_column_discovery_does_not_hide_failures(mocker, error):
    # Arrange
    client = mocker.Mock()
    client.run_sql.return_value = []
    if error:
        client.run_sql.side_effect = SnowflakeSqlError(error)

    # Act and assert
    if error == "Unexpected SQL failure":
        with pytest.raises(SnowflakeSqlError, match=error):
            get_grants_to_roles(client)
    else:
        assert get_grants_to_roles(client) is None
    assert client.run_sql.call_count == 1
