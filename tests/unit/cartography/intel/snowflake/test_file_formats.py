from unittest.mock import MagicMock

import pytest

import cartography.intel.snowflake.file_formats
from cartography.intel.snowflake.util import SnowflakeSqlError
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID


def test_get_file_formats_skips_a_database_it_may_not_read():
    # Arrange: Snowflake reports a missing privilege in the statement error.
    client = MagicMock(account_id=SNOWFLAKE_ACCOUNT_ID)
    client.run_sql.side_effect = SnowflakeSqlError(
        "Snowflake error 3001: Insufficient privileges to operate on database "
        "'SPRINGFIELD' (statement: SHOW FILE FORMATS IN DATABASE SPRINGFIELD)",
    )

    # Act
    rows, complete = cartography.intel.snowflake.file_formats.get(
        client, [{"database_name": "SPRINGFIELD", "name": "NUCLEAR_PLANT"}]
    )

    # Assert: the surface is skipped and reported, not turned into a sync failure.
    assert rows == []
    assert complete is False


def test_get_file_formats_reraises_an_unexpected_statement_failure():
    # Arrange
    client = MagicMock(account_id=SNOWFLAKE_ACCOUNT_ID)
    client.run_sql.side_effect = SnowflakeSqlError("Snowflake error 606: SQL execution")

    # Act and assert: anything that is not a missing feature or privilege has to
    # fail the sync rather than silently emptying the graph.
    with pytest.raises(SnowflakeSqlError):
        cartography.intel.snowflake.file_formats.get(
            client, [{"database_name": "SPRINGFIELD", "name": "NUCLEAR_PLANT"}]
        )
