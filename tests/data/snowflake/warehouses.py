"""Raw Snowflake warehouse payloads, as `GET /api/v2/warehouses` returns them."""

from typing import Any

SNOWFLAKE_WAREHOUSES: list[dict[str, Any]] = [
    {
        "name": "REACTOR_WH",
        "warehouse_type": "STANDARD",
        "size": "X-Large",
        "state": "STARTED",
        "min_cluster_count": 1,
        "max_cluster_count": 4,
        "scaling_policy": "STANDARD",
        "auto_suspend": 600,
        "auto_resume": True,
        "resource_monitor": "PLANT_BUDGET_MONITOR",
        "enable_query_acceleration": True,
        "max_concurrency_level": 8,
        "statement_timeout_in_seconds": 172800,
        "owner": "SYSADMIN",
        "owner_role_type": "ROLE",
        "budget": "SECTOR_7G_BUDGET",
        "kind": "PERMANENT",
        "comment": "Runs the reactor telemetry rollups",
        "created_on": "2026-08-03T16:00:00.000+00:00",
        "resumed_on": "2026-08-03T16:05:00.000+00:00",
        "updated_on": "2026-08-03T16:05:00.000+00:00",
    },
    # No resource monitor and no auto-suspend: this warehouse bills until someone
    # notices, and it has no credit ceiling to stop it.
    {
        "name": "DONUT_WH",
        "warehouse_type": "SNOWPARK-OPTIMIZED",
        # Older API versions spell the size field `warehouse_size`.
        "warehouse_size": "Medium",
        "state": "SUSPENDED",
        "min_cluster_count": 1,
        "max_cluster_count": 1,
        "scaling_policy": "ECONOMY",
        "auto_suspend": None,
        "auto_resume": False,
        "resource_monitor": None,
        "enable_query_acceleration": False,
        "max_concurrency_level": 8,
        "statement_timeout_in_seconds": 3600,
        "owner": "HOMER",
        "owner_role_type": "ROLE",
        "budget": None,
        "kind": "PERMANENT",
        "comment": None,
        "created_on": "2026-08-03T16:10:00.000+00:00",
        "resumed_on": None,
        "updated_on": "2026-08-03T16:10:00.000+00:00",
    },
]
