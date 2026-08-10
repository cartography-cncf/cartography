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


# SNOWFLAKE.ACCOUNT_USAGE rows, SQL-API shaped: every value arrives as a string and
# every column name lowercased. These describe the same account as the payloads
# above, so both paths must build the same graph.
#
# The account securable is named by the locator here too, and the role hierarchy is
# expressed as USAGE on a ROLE rather than as a separate listing.
SNOWFLAKE_ACCOUNT_USAGE_ROLES: list[dict[str, Any]] = [
    {
        "name": "ACCOUNTADMIN",
        "role_type": "ROLE",
        "role_database_name": None,
        "owner": "",
        "owner_role_type": None,
        "comment": "Account administrator can manage all aspects of the account.",
        "created_on": "2026-08-03T15:28:07.483+00:00",
    },
    {
        "name": "SYSADMIN",
        "role_type": "ROLE",
        "role_database_name": None,
        "owner": "",
        "owner_role_type": None,
        "comment": "Provides the ability to perform all operations.",
        "created_on": "2026-08-03T15:28:07.554+00:00",
    },
    {
        "name": "SAFETY_INSPECTOR",
        "role_type": "ROLE",
        "role_database_name": None,
        "owner": "USERADMIN",
        "owner_role_type": "ROLE",
        "comment": "Reads reactor telemetry",
        "created_on": "2026-08-03T15:40:00.000+00:00",
    },
    {
        "name": "REACTOR_READER",
        "role_type": "ROLE",
        "role_database_name": None,
        "owner": "USERADMIN",
        "owner_role_type": "ROLE",
        "comment": None,
        "created_on": "2026-08-03T15:41:00.000+00:00",
    },
    # A database role, which the same view returns alongside account roles and which
    # only ROLE_TYPE tells apart.
    {
        "name": "TELEMETRY_READER",
        "role_type": "DATABASE_ROLE",
        "role_database_name": "SPRINGFIELD_DB",
        "owner": "USERADMIN",
        "owner_role_type": "ROLE",
        "comment": "Database role scoped to SPRINGFIELD_DB",
        "created_on": "2026-08-03T15:48:00.000+00:00",
    },
    # An application role, which belongs to a Native App rather than to the account
    # and must not be loaded as either kind of role.
    {
        "name": "SOME_APP_ROLE",
        "role_type": "APPLICATION_ROLE",
        "role_database_name": None,
        "owner": "",
        "owner_role_type": None,
        "comment": None,
        "created_on": "2026-08-03T15:49:00.000+00:00",
    },
]

SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_ROLES: list[dict[str, Any]] = [
    {
        "privilege": "CREATE DATABASE",
        "granted_on": "ACCOUNT",
        "name": SNOWFLAKE_ACCOUNT_LOCATOR,
        "table_catalog": None,
        "table_schema": None,
        "granted_to": "ACCOUNT ROLE",
        "grantee_name": "SYSADMIN",
        "grant_option": "true",
        "granted_by": "",
        "created_on": "2026-08-03T15:28:07.565+00:00",
    },
    {
        "privilege": "CREATE WAREHOUSE",
        "granted_on": "ACCOUNT",
        "name": SNOWFLAKE_ACCOUNT_LOCATOR,
        "table_catalog": None,
        "table_schema": None,
        "granted_to": "ACCOUNT ROLE",
        "grantee_name": "SYSADMIN",
        "grant_option": "false",
        "granted_by": "",
        "created_on": "2026-08-03T15:28:07.568+00:00",
    },
    {
        "privilege": "CREATE COMPUTE POOL",
        "granted_on": "ACCOUNT",
        "name": SNOWFLAKE_ACCOUNT_LOCATOR,
        "table_catalog": None,
        "table_schema": None,
        "granted_to": "ACCOUNT ROLE",
        "grantee_name": "SYSADMIN",
        "grant_option": "false",
        "granted_by": "",
        "created_on": "2026-08-03T15:28:07.567+00:00",
    },
    {
        "privilege": "USAGE",
        "granted_on": "DATABASE",
        "name": "SPRINGFIELD_DB",
        "table_catalog": None,
        "table_schema": None,
        "granted_to": "ACCOUNT ROLE",
        "grantee_name": "SAFETY_INSPECTOR",
        "grant_option": "false",
        "granted_by": "USERADMIN",
        "created_on": "2026-08-03T15:42:00.000+00:00",
    },
    {
        "privilege": "SELECT",
        "granted_on": "TABLE",
        "name": "REACTOR_READINGS",
        "table_catalog": "SPRINGFIELD_DB",
        "table_schema": "NUCLEAR_PLANT",
        "granted_to": "ACCOUNT ROLE",
        "grantee_name": "SAFETY_INSPECTOR",
        "grant_option": "false",
        "granted_by": "USERADMIN",
        "created_on": "2026-08-03T15:43:00.000+00:00",
    },
    # `GRANT ROLE SYSADMIN TO ROLE ACCOUNTADMIN` as this view records it.
    {
        "privilege": "USAGE",
        "granted_on": "ROLE",
        "name": "SYSADMIN",
        "table_catalog": None,
        "table_schema": None,
        "granted_to": "ACCOUNT ROLE",
        "grantee_name": "ACCOUNTADMIN",
        "grant_option": "false",
        "granted_by": "",
        "created_on": "2026-08-03T15:28:07.554+00:00",
    },
    {
        "privilege": "USAGE",
        "granted_on": "ROLE",
        "name": "SAFETY_INSPECTOR",
        "table_catalog": None,
        "table_schema": None,
        "granted_to": "ACCOUNT ROLE",
        "grantee_name": "SYSADMIN",
        "grant_option": "false",
        "granted_by": "USERADMIN",
        "created_on": "2026-08-03T15:46:00.000+00:00",
    },
]

SNOWFLAKE_ACCOUNT_USAGE_GRANTS_TO_USERS: list[dict[str, Any]] = [
    {
        "role": "ACCOUNTADMIN",
        "granted_to": "USER",
        "grantee_name": "BURNS",
        "granted_by": "",
        "created_on": "2026-08-03T15:28:07.564+00:00",
    },
    {
        "role": "SAFETY_INSPECTOR",
        "granted_to": "USER",
        "grantee_name": "HOMER",
        "granted_by": "USERADMIN",
        "created_on": "2026-08-03T15:45:00.000+00:00",
    },
    {
        "role": "REACTOR_READER",
        "granted_to": "USER",
        "grantee_name": "SCRAM_BOT",
        "granted_by": "USERADMIN",
        "created_on": "2026-08-03T15:47:00.000+00:00",
    },
]

# A database role whose stored name is lowercase, meaning it was created quoted.
# ACCOUNT_USAGE reports the pair unquoted as `springfield_db.telemetry_peek`, while
# the role node's id is built through sf_fqn as `"springfield_db"."telemetry_peek"`.
# Requalifying is what keeps its grant edges attached.
SNOWFLAKE_ACCOUNT_USAGE_QUOTED_DATABASE_ROLE: list[dict[str, Any]] = [
    {
        "name": "telemetry_peek",
        "role_type": "DATABASE_ROLE",
        "role_database_name": "springfield_db",
        "owner": "USERADMIN",
        "owner_role_type": "ROLE",
        "comment": "Created with a quoted, lowercase name",
        "created_on": "2026-08-03T15:50:00.000+00:00",
    },
]

SNOWFLAKE_ACCOUNT_USAGE_QUOTED_DATABASE_ROLE_GRANTS: list[dict[str, Any]] = [
    {
        "privilege": "SELECT",
        "granted_on": "TABLE",
        "name": "REACTOR_READINGS",
        "table_catalog": "SPRINGFIELD_DB",
        "table_schema": "NUCLEAR_PLANT",
        "granted_to": "DATABASE_ROLE",
        "grantee_name": "springfield_db.telemetry_peek",
        "grant_option": "false",
        "granted_by": "USERADMIN",
        "created_on": "2026-08-03T15:51:00.000+00:00",
    },
]
