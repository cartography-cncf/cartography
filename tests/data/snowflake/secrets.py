"""Raw Snowflake secret payloads, as the per-schema listing returns them.

Snowflake never returns secret material through the API, so neither does this fixture.
"""

from typing import Any

SNOWFLAKE_SECRETS: list[dict[str, Any]] = [
    {
        "name": "DUFF_API_TOKEN",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "secret_type": "OAUTH2",
        "username": None,
        "oauth_scopes": ["orders.read", "orders.write"],
        "oauth_refresh_token_expiry_time": "2026-11-01T00:00:00.000+00:00",
        "api_authentication": "DUFF_OAUTH_INTEGRATION",
        "algorithm": None,
        "key_length": None,
        "owner": "SYSADMIN",
        "comment": "Token for the Duff ordering API",
        "created_on": "2026-08-03T17:00:00.000+00:00",
    },
    # A password secret. Older API versions spell the kind field `type`.
    {
        "name": "MOE_TAB_LOGIN",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "type": "PASSWORD",
        "username": "homer",
        "oauth_scopes": None,
        "oauth_refresh_token_expiry_time": None,
        "api_authentication": None,
        "algorithm": None,
        "key_length": None,
        "owner": "HOMER",
        "comment": None,
        "created_on": "2026-08-03T17:01:00.000+00:00",
    },
    {
        "name": "SQUISHEE_HMAC_KEY",
        "database_name": "SPRINGFIELD",
        "schema_name": "KWIK_E_MART",
        "secret_type": "SYMMETRIC_KEY",
        "username": None,
        "oauth_scopes": None,
        "oauth_refresh_token_expiry_time": None,
        "api_authentication": None,
        "algorithm": "AES",
        "key_length": 256,
        "owner": "SHOPKEEPER",
        "comment": None,
        "created_on": "2026-08-03T17:02:00.000+00:00",
    },
]
