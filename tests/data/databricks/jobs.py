from tests.data.databricks.sql_warehouses import DATABRICKS_WAREHOUSE_ID

# Shape returned by jobs.get() (the "jobs" list, with expand_tasks=true so each
# job's settings carry its full task graph).
DATABRICKS_JOBS = [
    {
        "job_id": 1011944831447606,
        "creator_user_name": "jeremy@subimage.io",
        "run_as_user_name": "jeremy@subimage.io",
        "created_time": 1782948408553,
        "settings": {
            "name": "carto-test-job",
            "format": "MULTI_TASK",
            "max_concurrent_runs": 1,
            "timeout_seconds": 0,
            "schedule": {
                "quartz_cron_expression": "0 0 12 * * ?",
                "timezone_id": "UTC",
                "pause_status": "PAUSED",
            },
            "tasks": [
                {
                    "task_key": "carto_task_nb",
                    "notebook_task": {
                        "notebook_path": "/Users/jeremy@subimage.io/carto_test_nb",
                        "source": "WORKSPACE",
                    },
                    "run_if": "ALL_SUCCESS",
                    "disabled": False,
                },
                {
                    "task_key": "refresh_pipeline",
                    "pipeline_task": {
                        "pipeline_id": "e66810c3-f9ba-4bbd-b9af-4e23bd2de755"
                    },
                    "sql_task": {"warehouse_id": DATABRICKS_WAREHOUSE_ID},
                    "run_if": "ALL_SUCCESS",
                },
            ],
        },
    },
    {
        # A job that runs as a service principal (matched by application_id).
        "job_id": 2022955942558717,
        "creator_user_name": "jeremy@subimage.io",
        "run_as_user_name": "abcd1234-5678-90ab-cdef-1234567890ab",
        "created_time": 1782948408553,
        "settings": {
            "name": "carto-sp-job",
            "format": "MULTI_TASK",
            "max_concurrent_runs": 1,
            "continuous": {"pause_status": "UNPAUSED"},
            "tasks": [
                {
                    "task_key": "sp_task",
                    "notebook_task": {"notebook_path": "/Shared/sp_nb"},
                    # Runs on a pre-existing all-purpose cluster.
                    "existing_cluster_id": "0202-cluster-aaaa",
                },
            ],
        },
    },
]
