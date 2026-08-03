"""SHOW REPLICATION GROUPS and SHOW FAILOVER GROUPS rows, SQL-API shaped."""

from typing import Any

SNOWFLAKE_REPLICATION_GROUPS: list[dict[str, Any]] = [
    {
        "created_on": "1784000000.000",
        "name": "REACTOR_REPLICA",
        "type": "REPLICATION",
        "is_primary": "true",
        "primary": "SPRINGFIELD.NUCLEAR.REACTOR_REPLICA",
        "object_types": "DATABASES, SHARES",
        "allowed_integration_types": "",
        # The first entry names a sibling account in the graph; the second names an
        # account outside the organization, which has no node.
        "allowed_accounts": "SPRINGFIELD.KWIKEMART, SHELBYVILLE.CITYHALL",
        "allowed_databases": "SPRINGFIELD",
        "allowed_shares": "REACTOR_FEED",
        "replication_schedule": "10 MINUTE",
        "secondary_state": "",
        "next_scheduled_refresh": "1785000000.000",
        "owner": "ACCOUNTADMIN",
        "comment": None,
    },
]

SNOWFLAKE_FAILOVER_GROUPS: list[dict[str, Any]] = [
    {
        "created_on": "1784500000.000",
        "name": "PLANT_FAILOVER",
        "type": "FAILOVER",
        "is_primary": "false",
        "primary": "SPRINGFIELD.KWIKEMART.PLANT_FAILOVER",
        # Replicating USERS and ROLES copies the account's identities elsewhere.
        "object_types": "DATABASES, USERS, ROLES",
        "allowed_integration_types": "SECURITY INTEGRATIONS",
        "allowed_accounts": "SPRINGFIELD.KWIKEMART",
        "allowed_databases": "",
        "allowed_shares": "",
        "replication_schedule": None,
        "secondary_state": "STARTED",
        "next_scheduled_refresh": None,
        "owner": "ACCOUNTADMIN",
        "comment": "disaster recovery",
    },
]
