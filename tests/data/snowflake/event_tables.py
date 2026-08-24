"""Raw Snowflake event table payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/event-tables` returns them. The
payload does not repeat its database and schema, so `get()` groups each listing under
the parent it was fetched for; `SNOWFLAKE_EVENT_TABLE_LISTINGS` is that shape.
"""

from typing import Any

SNOWFLAKE_EVENT_TABLES: list[dict[str, Any]] = [
    {
        "name": "PLANT_EVENTS",
        "rows": 9100000,
        "bytes": 734003200,
        "owner": "PLANT_ENGINEER",
        "comment": "Logs, traces and metrics from every plant procedure",
        "created_on": "2026-08-03T16:05:00.000+00:00",
    },
]

SNOWFLAKE_EVENT_TABLE_LISTINGS: list[dict[str, Any]] = [
    {
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "event_tables": SNOWFLAKE_EVENT_TABLES,
    },
]
