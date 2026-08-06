"""Raw Snowflake stream payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/streams` returns them. The
payload does not repeat its database and schema, so `get()` groups each listing under
the parent it was fetched for; `SNOWFLAKE_STREAM_LISTINGS` is that shape.
"""

from typing import Any

SNOWFLAKE_STREAMS: list[dict[str, Any]] = [
    # Source reported fully qualified, so it resolves to the table node.
    {
        "name": "REACTOR_READINGS_STREAM",
        "stream_source": "Table",
        "table_name": "SPRINGFIELD.NUCLEAR_PLANT.REACTOR_READINGS",
        "mode": "DEFAULT",
        "stale": False,
        "stale_after": "2026-08-17T16:15:00.000+00:00",
        "invalid_reason": None,
        "type": "DELTA",
        "owner": "PLANT_ENGINEER",
        "comment": "Feeds the coolant pipeline",
        "created_on": "2026-08-03T16:15:00.000+00:00",
    },
    # Stale: it has quietly stopped delivering changes.
    {
        "name": "SQUISHEE_SALES_STREAM",
        "stream_source": "Table",
        "table_name": "SPRINGFIELD.KWIK_E_MART.SQUISHEE_SALES",
        "mode": "APPEND_ONLY",
        "stale": True,
        "stale_after": "2026-07-20T16:15:00.000+00:00",
        "invalid_reason": "Base table dropped and recreated",
        "type": "DELTA",
        "owner": "SHOPKEEPER",
        "comment": None,
        "created_on": "2026-08-03T16:16:00.000+00:00",
    },
    # Sourced from a stage rather than a table, so no READS_FROM edge to a table.
    {
        "name": "LOG_STAGE_STREAM",
        "stream_source": "Stage",
        "table_name": None,
        "mode": "DEFAULT",
        "stale": False,
        "stale_after": "2026-08-17T16:17:00.000+00:00",
        "invalid_reason": None,
        "type": "DELTA",
        "owner": "PLANT_ENGINEER",
        "comment": None,
        "created_on": "2026-08-03T16:17:00.000+00:00",
    },
]

SNOWFLAKE_STREAM_LISTINGS: list[dict[str, Any]] = [
    {
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "streams": SNOWFLAKE_STREAMS,
    },
]
