"""Raw Snowflake Streamlit app payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/streamlits` returns them.
"""

from typing import Any

SNOWFLAKE_STREAMLITS: list[dict[str, Any]] = [
    {
        "name": "PLANT_DASHBOARD",
        "title": "Sector 7-G dashboard",
        "url_id": "dash123plant",
        "query_warehouse": "SECTOR_7G_WH",
        "compute_pool": "DONUT_POOL",
        "external_access_integrations": ["DUFF_EAI"],
        "main_file": "dashboard.py",
        "root_location": "@PLANT_STAGE/dashboard",
        "default_packages": ["streamlit", "pandas"],
        "owner": "PLANT_ENGINEER",
        "comment": "What the control room stares at",
        "created_on": "2026-08-03T17:00:00.000+00:00",
    },
    {
        "name": "SQUISHEE_TRACKER",
        "title": None,
        "url_id": "dash456kwik",
        "query_warehouse": None,
        "compute_pool": None,
        "external_access_integrations": [],
        "main_file": "squishee.py",
        "root_location": "@KWIK_E_STAGE/squishee",
        "default_packages": [],
        "owner": "SHOPKEEPER",
        "comment": None,
        "created_on": "2026-08-03T17:01:00.000+00:00",
    },
]
