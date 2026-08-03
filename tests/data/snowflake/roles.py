"""Raw Snowflake role and grant payloads.

Grant payloads are copied from the real API shape: `/roles/{r}/grants` returns one
row **per privilege**, not one row per object, and the account securable is named
by the account locator rather than the account identifier.
"""

from typing import Any

from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_LOCATOR

SNOWFLAKE_ROLES: list[dict[str, Any]] = [
    {
        "name": "ACCOUNTADMIN",
        "comment": "Account administrator can manage all aspects of the account.",
        "created_on": "2026-08-03T15:28:07.483+00:00",
        "owner": None,
        "assigned_to_users": 1,
        "granted_to_roles": 0,
        "granted_roles": 2,
    },
    {
        "name": "SYSADMIN",
        "comment": "Provides the ability to perform all operations.",
        "created_on": "2026-08-03T15:28:07.554+00:00",
        "owner": None,
        "assigned_to_users": 0,
        "granted_to_roles": 1,
        "granted_roles": 1,
    },
    {
        "name": "SAFETY_INSPECTOR",
        "comment": "Reads reactor telemetry",
        "created_on": "2026-08-03T15:40:00.000+00:00",
        "owner": "USERADMIN",
        "assigned_to_users": 2,
        "granted_to_roles": 1,
        "granted_roles": 1,
    },
    {
        "name": "REACTOR_READER",
        "comment": None,
        "created_on": "2026-08-03T15:41:00.000+00:00",
        "owner": "USERADMIN",
        "assigned_to_users": 1,
        "granted_to_roles": 1,
        "granted_roles": 0,
    },
]

# One row per privilege, exactly as the API returns them. SYSADMIN holds three
# account-level privileges, which must collapse into a single edge.
SNOWFLAKE_ROLE_GRANTS: dict[str, Any] = {
    "SYSADMIN": [
        {
            "securable": {
                "database": None,
                "schema": None,
                "service": None,
                "name": SNOWFLAKE_ACCOUNT_LOCATOR,
            },
            "containing_scope": None,
            "securable_type": "ACCOUNT",
            "grant_option": True,
            "privileges": ["CREATE DATABASE"],
            "created_on": "2026-08-03T15:28:07.565+00:00",
            "granted_by": "",
        },
        {
            "securable": {
                "database": None,
                "schema": None,
                "service": None,
                "name": SNOWFLAKE_ACCOUNT_LOCATOR,
            },
            "securable_type": "ACCOUNT",
            "grant_option": False,
            "privileges": ["CREATE WAREHOUSE"],
            "created_on": "2026-08-03T15:28:07.568+00:00",
            "granted_by": "",
        },
        {
            "securable": {
                "database": None,
                "schema": None,
                "service": None,
                "name": SNOWFLAKE_ACCOUNT_LOCATOR,
            },
            "securable_type": "ACCOUNT",
            "grant_option": False,
            "privileges": ["CREATE COMPUTE POOL"],
            "created_on": "2026-08-03T15:28:07.567+00:00",
            "granted_by": "",
        },
    ],
    "SAFETY_INSPECTOR": [
        {
            "securable": {"database": None, "schema": None, "name": "SPRINGFIELD_DB"},
            "securable_type": "DATABASE",
            "grant_option": False,
            "privileges": ["USAGE"],
            "created_on": "2026-08-03T15:42:00.000+00:00",
            "granted_by": "USERADMIN",
        },
        {
            "securable": {
                "database": "SPRINGFIELD_DB",
                "schema": "NUCLEAR_PLANT",
                "name": "REACTOR_READINGS",
            },
            "securable_type": "TABLE",
            "grant_option": False,
            "privileges": ["SELECT"],
            "created_on": "2026-08-03T15:43:00.000+00:00",
            "granted_by": "USERADMIN",
        },
        # A grant on an object type Cartography does not model, which must be
        # skipped and counted rather than producing a dangling edge.
        {
            "securable": {"database": None, "schema": None, "name": "WEIRD_THING"},
            "securable_type": "SOME FUTURE OBJECT",
            "grant_option": False,
            "privileges": ["USAGE"],
            "created_on": "2026-08-03T15:44:00.000+00:00",
            "granted_by": "USERADMIN",
        },
    ],
    "ACCOUNTADMIN": [],
    "REACTOR_READER": [],
}

# `grants-of` carries both the user assignments and the role hierarchy.
SNOWFLAKE_ROLE_GRANTS_OF: dict[str, Any] = {
    "ACCOUNTADMIN": [
        {
            "created_on": "2026-08-03T15:28:07.564+00:00",
            "role": "ACCOUNTADMIN",
            "granted_to": "USER",
            "grantee_name": "BURNS",
            "granted_by": "",
        },
    ],
    "SYSADMIN": [
        {
            "created_on": "2026-08-03T15:28:07.554+00:00",
            "role": "SYSADMIN",
            "granted_to": "ROLE",
            "grantee_name": "ACCOUNTADMIN",
            "granted_by": "",
        },
    ],
    "SAFETY_INSPECTOR": [
        {
            "created_on": "2026-08-03T15:45:00.000+00:00",
            "role": "SAFETY_INSPECTOR",
            "granted_to": "USER",
            "grantee_name": "HOMER",
            "granted_by": "USERADMIN",
        },
        {
            "created_on": "2026-08-03T15:46:00.000+00:00",
            "role": "SAFETY_INSPECTOR",
            "granted_to": "ROLE",
            "grantee_name": "SYSADMIN",
            "granted_by": "USERADMIN",
        },
    ],
    "REACTOR_READER": [
        # Granted to a service user, which must land on SnowflakeServiceUser.
        {
            "created_on": "2026-08-03T15:47:00.000+00:00",
            "role": "REACTOR_READER",
            "granted_to": "USER",
            "grantee_name": "SCRAM_BOT",
            "granted_by": "USERADMIN",
        },
    ],
}
