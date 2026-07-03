# Shape returned by pipelines.get() (each pipeline's detail, incl. its spec).
DATABRICKS_PIPELINES = [
    {
        "pipeline_id": "e66810c3-f9ba-4bbd-b9af-4e23bd2de755",
        "name": "carto-test-pipeline",
        "state": "IDLE",
        "creator_user_name": "jeremy@subimage.io",
        "run_as_user_name": "jeremy@subimage.io",
        "spec": {
            "id": "e66810c3-f9ba-4bbd-b9af-4e23bd2de755",
            "name": "carto-test-pipeline",
            "catalog": "workspace",
            "schema": "carto_test_schema",
            "continuous": False,
            "development": True,
            "serverless": True,
            "pipeline_type": "WORKSPACE",
            "libraries": [
                {"notebook": {"path": "/Users/jeremy@subimage.io/carto_test_nb"}},
            ],
        },
    },
]
