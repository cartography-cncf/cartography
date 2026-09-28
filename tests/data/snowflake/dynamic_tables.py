"""Raw Snowflake dynamic table payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/dynamic-tables` returns them.
The payload does not repeat its database and schema, so `get()` groups each listing
under the parent it was fetched for; `SNOWFLAKE_DYNAMIC_TABLE_LISTINGS` is that shape.
"""

from typing import Any

SNOWFLAKE_DYNAMIC_TABLES: list[dict[str, Any]] = [
    {
        "name": "COOLANT_TRENDS",
        "warehouse": "DUFF_WH",
        "target_lag": "20 minutes",
        "refresh_mode": "INCREMENTAL",
        "query": (
            "SELECT date_trunc('hour', recorded_at) AS hour, avg(core_temp_c) "
            "FROM reactor_readings GROUP BY 1"
        ),
        "scheduling_state": "RUNNING",
        "owner": "PLANT_ENGINEER",
        "comment": "Hourly coolant averages",
        "created_on": "2026-08-03T16:00:00.000+00:00",
    },
    # Suspended, so it keeps serving stale rows without any query failing.
    {
        "name": "MELTDOWN_ALERTS",
        "warehouse": "DUFF_WH",
        "target_lag": "1 minute",
        "refresh_mode": "FULL",
        "query": "SELECT * FROM reactor_readings WHERE core_temp_c > 900",
        "scheduling_state": "SUSPENDED",
        "owner": "PLANT_ENGINEER",
        "comment": None,
        "created_on": "2026-08-03T16:01:00.000+00:00",
    },
]

SNOWFLAKE_DYNAMIC_TABLE_LISTINGS: list[dict[str, Any]] = [
    {
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "dynamic_tables": SNOWFLAKE_DYNAMIC_TABLES,
    },
]
