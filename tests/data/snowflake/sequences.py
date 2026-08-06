"""Raw Snowflake sequence payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/sequences` returns them. The
payload does not repeat its database and schema, so `get()` groups each listing under
the parent it was fetched for; `SNOWFLAKE_SEQUENCE_LISTINGS` is that shape.
"""

from typing import Any

SNOWFLAKE_SEQUENCES: list[dict[str, Any]] = [
    {
        "name": "EMPLOYEE_ID_SEQ",
        "start_value": 1,
        "increment": 1,
        "next_value": 743,
        "owner": "SYSADMIN",
        "comment": "Surrogate keys for plant staff",
        "created_on": "2026-08-03T16:20:00.000+00:00",
    },
]

SNOWFLAKE_SEQUENCE_LISTINGS: list[dict[str, Any]] = [
    {
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "sequences": SNOWFLAKE_SEQUENCES,
    },
]
