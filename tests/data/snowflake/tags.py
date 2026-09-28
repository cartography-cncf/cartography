"""Raw Snowflake tag definition payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/tags` returns them: one tag
constrained to a fixed vocabulary and one that accepts any value at all.
"""

from typing import Any

SNOWFLAKE_TAGS: list[dict[str, Any]] = [
    {
        "name": "SAFETY_CLASSIFICATION",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "allowed_values": ["PUBLIC", "RESTRICTED", "SECRET"],
        "owner": "PLANT_ENGINEER",
        "comment": "How closely guarded the data is",
        "created_on": "2026-08-03T17:10:00.000+00:00",
    },
    {
        "name": "COST_CENTER",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "allowed_values": [],
        "owner": "SHOPKEEPER",
        "comment": None,
        "created_on": "2026-08-03T17:11:00.000+00:00",
    },
]
