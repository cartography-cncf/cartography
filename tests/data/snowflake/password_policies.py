"""Password policy listing rows plus their DESCRIBE settings, SQL-API shaped.

This is the shape ``password_policies.get()`` returns: the ``SHOW`` row with the
``DESCRIBE`` output attached under ``settings``. Every value is still a string.
"""

from typing import Any

SNOWFLAKE_PASSWORD_POLICIES: list[dict[str, Any]] = [
    {
        "created_on": "1780000000.000",
        "name": "STRICT_PASSWORDS",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "kind": "PASSWORD_POLICY",
        "owner": "SAFETY_INSPECTOR",
        "owner_role_type": "ROLE",
        "comment": "baseline password policy",
        "settings": {
            "password_min_length": "14",
            "password_max_length": "256",
            "password_min_upper_case_chars": "1",
            "password_min_lower_case_chars": "1",
            "password_min_numeric_chars": "1",
            "password_min_special_chars": "1",
            "password_min_age_days": "0",
            "password_max_age_days": "90",
            "password_max_retries": "5",
            "password_lockout_time_mins": "15",
            "password_history": "5",
        },
    },
    {
        "created_on": "1781000000.000",
        "name": "LEGACY_PASSWORDS",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "kind": "PASSWORD_POLICY",
        "owner": "SAFETY_INSPECTOR",
        "owner_role_type": "ROLE",
        "comment": None,
        "settings": {
            "password_min_length": "8",
            "password_max_age_days": "0",
            "password_max_retries": "",
        },
    },
]
