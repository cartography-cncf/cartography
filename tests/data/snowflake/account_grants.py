"""SHOW GRANTS ON ACCOUNT rows, as the SQL API returns them.

``name`` is the account *locator*, not the organization-qualified identifier the
account node is keyed on, which is why the transform ignores it.
"""

from typing import Any

from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_LOCATOR

SNOWFLAKE_ACCOUNT_GRANTS: list[dict[str, Any]] = [
    {
        "created_on": "1780000000.000",
        "privilege": "MANAGE GRANTS",
        "granted_on": "ACCOUNT",
        "name": SNOWFLAKE_ACCOUNT_LOCATOR,
        "granted_to": "ROLE",
        "grantee_name": "SAFETY_INSPECTOR",
        "grant_option": "false",
        "granted_by": "ACCOUNTADMIN",
    },
    {
        "created_on": "1780000000.000",
        "privilege": "CREATE USER",
        "granted_on": "ACCOUNT",
        "name": SNOWFLAKE_ACCOUNT_LOCATOR,
        "granted_to": "ROLE",
        "grantee_name": "SAFETY_INSPECTOR",
        "grant_option": "true",
        "granted_by": "ACCOUNTADMIN",
    },
    {
        "created_on": "1780000000.000",
        "privilege": "CREATE DATABASE",
        "granted_on": "ACCOUNT",
        "name": SNOWFLAKE_ACCOUNT_LOCATOR,
        "granted_to": "ROLE",
        "grantee_name": "SYSADMIN",
        "grant_option": "false",
        "granted_by": "ACCOUNTADMIN",
    },
    {
        # Not a role grantee, so it cannot resolve to a principal node.
        "created_on": "1780000000.000",
        "privilege": "IMPORTED PRIVILEGES",
        "granted_on": "ACCOUNT",
        "name": SNOWFLAKE_ACCOUNT_LOCATOR,
        "granted_to": "DATABASE_ROLE",
        "grantee_name": "SPRINGFIELD.REACTOR_READER",
        "grant_option": "false",
        "granted_by": "ACCOUNTADMIN",
    },
]
