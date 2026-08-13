"""Raw Snowflake network rule payloads, as the per-schema listing returns them."""

from typing import Any

SNOWFLAKE_NETWORK_RULES: list[dict[str, Any]] = [
    {
        "name": "PLANT_OFFICE_IPS",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "type": "IPV4",
        "mode": "INGRESS",
        "value_list": ["192.0.2.0/24", "198.51.100.14"],
        "owner": "SECURITYADMIN",
        "comment": "Sector 7-G office range",
        "created_on": "2026-08-03T16:30:00.000+00:00",
    },
    # An egress rule: this is what an external access integration allows handler code
    # to call out to.
    {
        "name": "DUFF_API_EGRESS",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "type": "HOST_PORT",
        "mode": "EGRESS",
        "value_list": ["api.duff.example.com:443"],
        "owner": "SYSADMIN",
        "comment": None,
        "created_on": "2026-08-03T16:31:00.000+00:00",
    },
    {
        "name": "SQUISHEE_VPCE",
        "database_name": "SPRINGFIELD",
        "schema_name": "KWIK_E_MART",
        "type": "AWSVPCEID",
        "mode": "INGRESS",
        "value_list": ["vpce-0123456789abcdef0"],
        "owner": "SHOPKEEPER",
        "comment": None,
        "created_on": "2026-08-03T16:32:00.000+00:00",
    },
]
