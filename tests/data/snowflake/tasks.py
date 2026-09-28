"""Raw Snowflake task payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/tasks` returns them: one
scheduled root task and one child task triggered by it, which together form the
smallest possible task DAG.
"""

from typing import Any

SNOWFLAKE_TASKS: list[dict[str, Any]] = [
    {
        "name": "SCRAM_CHECK",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "warehouse": "SECTOR_7G_WH",
        "schedule": "USING CRON */5 * * * * UTC",
        "state": "started",
        "definition": "INSERT INTO SAFETY_LOG SELECT CORE_TEMP_C FROM REACTOR_READINGS",
        "predecessors": [],
        "condition": None,
        "allow_overlapping_execution": False,
        "error_integration": "MELTDOWN_ALERTS",
        "success_integration": None,
        "execute_as": "OWNER",
        "suspend_task_after_num_failures": 3,
        "target_completion_interval": None,
        "user_task_managed_initial_warehouse_size": None,
        "owner": "PLANT_ENGINEER",
        "owner_role_type": "ROLE",
        "comment": "Trip the reactor when the core runs hot",
        "created_on": "2026-08-03T16:00:00.000+00:00",
    },
    {
        "name": "COOLANT_TOPUP",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "warehouse": None,
        "schedule": None,
        "state": "suspended",
        "definition": "CALL SCRAM_REACTOR('COOLANT')",
        "predecessors": ["SPRINGFIELD.NUCLEAR_PLANT.SCRAM_CHECK"],
        "condition": "SYSTEM$STREAM_HAS_DATA('COOLANT_STREAM')",
        "allow_overlapping_execution": True,
        "error_integration": None,
        "success_integration": "DONUT_NOTIFY",
        "execute_as": "CALLER",
        "suspend_task_after_num_failures": 0,
        "target_completion_interval": "10 MINUTES",
        "user_task_managed_initial_warehouse_size": "XSMALL",
        "owner": "PLANT_ENGINEER",
        "owner_role_type": "ROLE",
        "comment": None,
        "created_on": "2026-08-03T16:05:00.000+00:00",
    },
]
