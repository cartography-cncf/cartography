"""Raw Snowflake alert payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/alerts` returns them.
"""

from typing import Any

SNOWFLAKE_ALERTS: list[dict[str, Any]] = [
    {
        "name": "MELTDOWN_WATCH",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "warehouse": "SECTOR_7G_WH",
        "schedule": "1 MINUTE",
        "state": "started",
        "condition": "SELECT 1 FROM REACTOR_READINGS WHERE CORE_TEMP_C > 900",
        "action": "CALL SCRAM_REACTOR('OVERHEAT')",
        "owner": "PLANT_ENGINEER",
        "comment": "Page the safety inspector",
        "created_on": "2026-08-03T16:40:00.000+00:00",
    },
    {
        "name": "DONUT_SHORTAGE",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "warehouse": None,
        "schedule": "USING CRON 0 7 * * * UTC",
        "state": "suspended",
        "condition": "SELECT 1 FROM DONUT_DELIVERIES WHERE BOXES < 1",
        "action": "INSERT INTO BREAKROOM_LOG VALUES ('no donuts')",
        "owner": "SHOPKEEPER",
        "comment": None,
        "created_on": "2026-08-03T16:41:00.000+00:00",
    },
]
