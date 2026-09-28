"""SHOW SHARES, SHOW GRANTS TO SHARE and SHOW GRANTS OF SHARE rows, SQL-API shaped."""

from typing import Any

SNOWFLAKE_SHARES: list[dict[str, Any]] = [
    {
        "created_on": "1782000000.000",
        "kind": "OUTBOUND",
        "owner_account": "SPRINGFIELD.NUCLEAR",
        "name": "REACTOR_FEED",
        "database_name": "SPRINGFIELD",
        "to": "SPRINGFIELD.SHELBYVILLE_READER, SHELBYVILLE.CITYHALL",
        "owner": "ACCOUNTADMIN",
        "comment": "daily reactor telemetry",
        "listing_global_name": "GZTDUFF0001",
    },
    {
        # An inbound share: this account consumes it, so its grants are not readable
        # from here and must not be requested.
        "created_on": "1782500000.000",
        "kind": "INBOUND",
        "owner_account": "SNOW.SFC_SAMPLES",
        "name": "SAMPLE_DATA",
        "database_name": "SNOWFLAKE_SAMPLE_DATA",
        "to": "",
        "owner": "",
        "comment": None,
        "listing_global_name": None,
    },
    {
        # A second inbound share carrying the *same* name from a different provider.
        # Keyed on the name alone these two would collapse onto one node, and neither
        # would match the id rebuilt from its database's `origin`.
        "created_on": "1782600000.000",
        "kind": "INBOUND",
        "owner_account": "SHELBYVILLE.CITYHALL",
        "name": "SAMPLE_DATA",
        "database_name": "SHELBYVILLE_SAMPLE_DATA",
        "to": "",
        "owner": "",
        "comment": None,
        "listing_global_name": None,
    },
]

SNOWFLAKE_SHARE_GRANTS: dict[str, Any] = {
    "REACTOR_FEED": [
        {
            "created_on": "1782000000.000",
            "privilege": "USAGE",
            "granted_on": "DATABASE",
            "name": "SPRINGFIELD",
            "granted_to": "SHARE",
            "grantee_name": "REACTOR_FEED",
        },
        {
            "created_on": "1782000000.000",
            "privilege": "SELECT",
            "granted_on": "TABLE",
            "name": "SPRINGFIELD.NUCLEAR_PLANT.REACTOR_READINGS",
            "granted_to": "SHARE",
            "grantee_name": "REACTOR_FEED",
        },
        {
            # An object type Cartography does not model: counted and skipped, not
            # fatal.
            "created_on": "1782000000.000",
            "privilege": "USAGE",
            "granted_on": "CORTEX SEARCH SERVICE",
            "name": "SPRINGFIELD.NUCLEAR_PLANT.DONUT_SEARCH",
            "granted_to": "SHARE",
            "grantee_name": "REACTOR_FEED",
        },
    ],
}

SNOWFLAKE_SHARE_CONSUMERS: dict[str, Any] = {
    "REACTOR_FEED": [
        {
            "created_on": "1782100000.000",
            "share": "SPRINGFIELD.NUCLEAR.REACTOR_FEED",
            "granted_to": "ACCOUNT",
            "grantee_name": "SPRINGFIELD.SHELBYVILLE_READER",
            "granted_by": "ACCOUNTADMIN",
        },
    ],
}
