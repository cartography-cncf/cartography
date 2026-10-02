import json

import pytest
import requests

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
    grants, assignments, inherited_rows = split_grants([ordinary, inherited], [])

    # Assert
    assert list(grants) == ["INVENTORY_READER"]
    assert len(grants["INVENTORY_READER"]) == 1
    assert grants["INVENTORY_READER"][0]["securable"]["name"] == "EXAMPLE_TABLE"
    assert grants["INVENTORY_READER"][0]["privileges"] == ["REFERENCES"]
    assert assignments == {}
    assert inherited_rows == [inherited]


def _sql_error(message, code="000904"):
    response = requests.Response()
    response.status_code = 422
    response._content = json.dumps({"code": code, "message": message}).encode()
    error = SnowflakeSqlError(message)
    error.__cause__ = requests.HTTPError(response=response)
    return error


@pytest.mark.parametrize("has_inherited", [False, True])
def test_grant_query_projects_only_supported_columns(mocker, has_inherited):
    # Arrange
    client = mocker.Mock()
    rows = [{"privilege": "REFERENCES"}]
    client.run_sql.side_effect = (
        [rows]
        if has_inherited
        else [
            _sql_error("SQL compilation error: invalid identifier 'IS_INHERITED'"),
            rows,
        ]
    )

    # Act
    result = get_grants_to_roles(client)

    # Assert
    assert result == rows
    assert client.run_sql.call_count == (1 if has_inherited else 2)
    statement = client.run_sql.call_args.args[0].lower()
    projection = statement.split("\nfrom", 1)[0]
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
        expected_columns.update(
            {
                "is_inherited",
                "inherited_from",
                "inherited_from_database",
                "inherited_from_schema",
            }
        )
    assert projected_columns == expected_columns
    assert "where deleted_on is null" in statement
    assert all(
        call.args[0].lstrip().startswith("SELECT")
        for call in client.run_sql.call_args_list
    )


@pytest.mark.parametrize(
    "message,code",
    [
        ("invalid identifier 'GRANTEE_NAME'", "000904"),
        ("invalid identifier 'IS_INHERITED'", "000604"),
        ("Unexpected SQL failure", "000904"),
    ],
)
def test_grant_query_does_not_hide_unexpected_failures(mocker, message, code):
    # Arrange
    client = mocker.Mock()
    client.run_sql.side_effect = _sql_error(message, code)

    # Act and assert
    with pytest.raises(SnowflakeSqlError):
        get_grants_to_roles(client)
    assert client.run_sql.call_count == 1


def test_unreadable_grant_view_still_reports_incomplete(mocker):
    # Arrange
    client = mocker.Mock()
    client.run_sql.side_effect = _sql_error("Insufficient privileges", "003001")

    # Act and assert
    assert get_grants_to_roles(client) is None
    assert client.run_sql.call_count == 1


def test_grant_query_supports_source_account_layout(mocker):
    # Arrange
    client = mocker.Mock()
    rows = [{"is_inherited": True, "inherited_from": "ACCOUNT"}]
    client.run_sql.side_effect = [
        _sql_error("SQL compilation error: invalid identifier 'INHERITED_FROM'"),
        rows,
    ]

    # Act
    result = get_grants_to_roles(client)

    # Assert
    assert result == rows
    assert client.run_sql.call_count == 2
    statement = " ".join(client.run_sql.call_args.args[0].lower().split())
    assert "is_inherited," in statement
    assert (
        "case when inherited_from_schema is not null then 'schema' "
        "when inherited_from_database is not null then 'database' "
        "when inherited_from_account is not null then 'account' "
        "end as inherited_from" in statement
    )
    assert "inherited_from_database, inherited_from_schema from" in statement
    assert "*" not in statement


def test_missing_source_scope_columns_does_not_drop_inheritance(mocker):
    # Arrange
    client = mocker.Mock()
    client.run_sql.side_effect = [
        _sql_error("invalid identifier 'INHERITED_FROM'"),
        _sql_error("invalid identifier 'INHERITED_FROM_ACCOUNT'"),
    ]

    # Act and assert
    with pytest.raises(SnowflakeSqlError):
        get_grants_to_roles(client)
    assert client.run_sql.call_count == 2


@pytest.mark.parametrize("kind", ["ROLE", "DATABASE_ROLE"])
def test_inherited_flag_does_not_drop_role_hierarchy(kind):
    # Arrange
    row = {
        "privilege": "USAGE",
        "granted_on": kind,
        "name": "READER",
        "table_catalog": "EXAMPLE_DB",
        "granted_to": "ROLE",
        "grantee_name": "PARENT",
        "is_inherited": True,
    }

    # Act
    direct, assignments, inherited = split_grants([row], [])

    # Assert
    granted_role = "READER" if kind == "ROLE" else "EXAMPLE_DB.READER"
    assert direct["PARENT"][0]["privileges"] == ["USAGE"]
    assert assignments[granted_role][0]["grantee_name"] == "PARENT"
    assert inherited == []
