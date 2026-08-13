"""SHOW PARAMETERS IN ACCOUNT rows, as the SQL API returns them.

An empty ``value`` means the parameter is unset, and ``level`` is empty when nobody
has ever set it.
"""

from typing import Any

SNOWFLAKE_ACCOUNT_PARAMETERS: list[dict[str, Any]] = [
    {
        "key": "NETWORK_POLICY",
        "value": "PLANT_PERIMETER",
        "default": "",
        "level": "ACCOUNT",
        "description": "Specifies the network policy in effect for the account.",
        "type": "STRING",
    },
    {
        "key": "PREVENT_UNLOAD_TO_INLINE_URL",
        "value": "false",
        "default": "false",
        "level": "",
        "description": "Whether to prevent ad hoc data unload to an external URL.",
        "type": "BOOLEAN",
    },
    {
        "key": "REQUIRE_STORAGE_INTEGRATION_FOR_STAGE_CREATION",
        "value": "true",
        "default": "false",
        "level": "ACCOUNT",
        "description": "Whether stage creation requires a storage integration.",
        "type": "BOOLEAN",
    },
    {
        # Not security relevant, so it must not become a node.
        "key": "STATEMENT_TIMEOUT_IN_SECONDS",
        "value": "172800",
        "default": "172800",
        "level": "",
        "description": "Time in seconds after which a running statement is aborted.",
        "type": "NUMBER",
    },
]

SNOWFLAKE_NETWORK_POLICY_PARAMETERS: list[dict[str, Any]] = [
    {
        "key": "NETWORK_POLICY",
        "value": "PLANT_PERIMETER",
        "default": "",
        "level": "ACCOUNT",
        "description": "Specifies the network policy in effect for the account.",
        "type": "STRING",
    },
]
