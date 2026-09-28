"""Raw Snowflake compute pool payloads, as `GET /api/v2/compute-pools` returns them."""

from typing import Any

SNOWFLAKE_COMPUTE_POOLS: list[dict[str, Any]] = [
    {
        "name": "MONORAIL_POOL",
        "min_nodes": 1,
        "max_nodes": 3,
        "instance_family": "CPU_X64_S",
        "state": "ACTIVE",
        "num_services": 2,
        "num_jobs": 0,
        "active_nodes": 2,
        "owner": "SYSADMIN",
        "is_exclusive": False,
        "application": None,
        "auto_resume": True,
        "auto_suspend_secs": 3600,
        "created_on": "2026-08-03T16:20:00.000+00:00",
        "comment": "Runs the monorail telemetry services",
    },
    # A pool dedicated to a Native App: its nodes are not available to the account's
    # own services.
    {
        "name": "KWIK_E_MART_POOL",
        "min_nodes": 1,
        "max_nodes": 1,
        "instance_family": "GPU_NV_S",
        "state": "SUSPENDED",
        "num_services": 0,
        "num_jobs": 0,
        "active_nodes": 0,
        "owner": "SHOPKEEPER",
        "is_exclusive": True,
        "application": "SQUISHEE_FORECASTER",
        "auto_resume": False,
        "auto_suspend_secs": 600,
        "created_on": "2026-08-03T16:22:00.000+00:00",
        "comment": None,
    },
]
