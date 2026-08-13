"""Raw Snowflake notebook payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/notebooks` returns them.
"""

from typing import Any

SNOWFLAKE_NOTEBOOKS: list[dict[str, Any]] = [
    {
        "name": "REACTOR_FORECAST",
        "title": "Reactor forecast",
        "query_warehouse": "SECTOR_7G_WH",
        "compute_pool": "DONUT_POOL",
        "external_access_integrations": ["DUFF_EAI"],
        "external_access_secrets": {"cred": "SPRINGFIELD.NUCLEAR_PLANT.DUFF_TOKEN"},
        "runtime_name": "SYSTEM$BASIC_RUNTIME",
        "default_version": "LIVE",
        "main_file": "forecast.ipynb",
        "url_id": "abc123donut",
        "import_urls": ["@PLANT_STAGE/notebooks/"],
        "live_version_location_uri": "snow://notebook/REACTOR_FORECAST/versions/live",
        "owner": "PLANT_ENGINEER",
        "comment": "Where the core temperature is heading",
        "created_on": "2026-08-03T16:50:00.000+00:00",
    },
    {
        "name": "DONUT_TRENDS",
        "title": None,
        "query_warehouse": None,
        "compute_pool": None,
        "external_access_integrations": [],
        "external_access_secrets": {},
        "runtime_name": None,
        "default_version": "VERSION$1",
        "main_file": "donuts.ipynb",
        "url_id": "xyz789donut",
        "import_urls": [],
        "live_version_location_uri": None,
        "owner": "SHOPKEEPER",
        "comment": None,
        "created_on": "2026-08-03T16:51:00.000+00:00",
    },
]
