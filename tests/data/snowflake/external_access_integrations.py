"""Raw Snowflake external access integration rows, as `SHOW EXTERNAL ACCESS INTEGRATIONS` returns them.

The SQL API renders the allow-lists as bracketed strings rather than JSON arrays, which
is what the fixture reproduces.
"""

from typing import Any

SNOWFLAKE_EXTERNAL_ACCESS_INTEGRATIONS: list[dict[str, Any]] = [
    {
        "name": "DUFF_API_ACCESS",
        "type": "EXTERNAL_ACCESS",
        "category": "SECURITY",
        "enabled": "true",
        "allowed_network_rules": "[SPRINGFIELD.NUCLEAR_PLANT.DUFF_API_EGRESS]",
        "allowed_api_authentication_integrations": "[DUFF_OAUTH_INTEGRATION]",
        "allowed_authentication_secrets": (
            "[SPRINGFIELD.NUCLEAR_PLANT.DUFF_API_TOKEN]"
        ),
        "comment": "Lets the ordering procedure call the Duff API",
        "created_on": "1784700000.000000000 0",
    },
    # Disabled and allowing nothing: handler code using it cannot reach the network.
    {
        "name": "MOE_TAB_ACCESS",
        "type": "EXTERNAL_ACCESS",
        "category": "SECURITY",
        "enabled": "false",
        "allowed_network_rules": "[]",
        "allowed_api_authentication_integrations": "",
        "allowed_authentication_secrets": "",
        "comment": "",
        "created_on": "1784800000.000000000 0",
    },
]
