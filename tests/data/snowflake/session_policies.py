"""Session policy listing rows plus their DESCRIBE settings, SQL-API shaped."""

from typing import Any

SNOWFLAKE_SESSION_POLICIES: list[dict[str, Any]] = [
    {
        "created_on": "1780500000.000",
        "name": "SHORT_SESSIONS",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "kind": "SESSION_POLICY",
        "owner": "SAFETY_INSPECTOR",
        "owner_role_type": "ROLE",
        "comment": "tighten idle timeouts",
        "settings": {
            "session_idle_timeout_mins": "30",
            "session_ui_idle_timeout_mins": "10",
            "allowed_secondary_authentication_methods": "[PASSWORD]",
        },
    },
    {
        "created_on": "1780600000.000",
        "name": "DEFAULT_SESSIONS",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "kind": "SESSION_POLICY",
        "owner": "SAFETY_INSPECTOR",
        "owner_role_type": "ROLE",
        "comment": None,
        "settings": {
            "session_idle_timeout_mins": "240",
            "session_ui_idle_timeout_mins": "",
            "allowed_secondary_authentication_methods": None,
        },
    },
]
