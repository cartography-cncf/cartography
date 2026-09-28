"""Authentication policy listing rows plus their DESCRIBE settings, SQL-API shaped."""

from typing import Any

SNOWFLAKE_AUTHENTICATION_POLICIES: list[dict[str, Any]] = [
    {
        "created_on": "1780700000.000",
        "name": "REQUIRE_MFA",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "kind": "AUTHENTICATION_POLICY",
        "owner": "SAFETY_INSPECTOR",
        "owner_role_type": "ROLE",
        "comment": "humans must use MFA",
        "settings": {
            "authentication_methods": "[PASSWORD, SAML]",
            "mfa_authentication_methods": "[PASSWORD]",
            "mfa_enrollment": "REQUIRED",
            "client_types": "[SNOWFLAKE_UI, DRIVERS]",
            "security_integrations": "[ALL]",
            "pat_policy": "",
        },
    },
    {
        "created_on": "1780800000.000",
        "name": "SERVICE_AUTH",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "kind": "AUTHENTICATION_POLICY",
        "owner": "SAFETY_INSPECTOR",
        "owner_role_type": "ROLE",
        "comment": None,
        "settings": {
            "authentication_methods": "[KEYPAIR, PROGRAMMATIC_ACCESS_TOKEN]",
            "mfa_authentication_methods": None,
            "mfa_enrollment": "OPTIONAL",
            "client_types": "[ALL]",
            "security_integrations": "[ALL]",
            "pat_policy": "NETWORK_POLICY_EVALUATION = ENFORCED_REQUIRED",
        },
    },
]
