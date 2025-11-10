MOCK_INSTANCES = {
    "items": [
        {
            "selfLink": "projects/test-project/instances/carto-sql-test-instance",
            "name": "carto-sql-test-instance",
            "databaseVersion": "POSTGRES_15",
            "region": "us-central1",
            "gceZone": "us-central1-a",
            "state": "RUNNABLE",
            "backendType": "SECOND_GEN",
            "settings": {
                "ipConfiguration": {
                    "privateNetwork": "projects/test-project/global/networks/carto-sql-vpc",
                },
            },
            "serviceAccountEmailAddress": "test-sa@test-project.iam.gserviceaccount.com",
        },
    ],
}

MOCK_DATABASES = {
    "items": [
        {
            "name": "carto-db-1",
            "charset": "UTF8",
            "collation": "en_US.UTF8",
            "instance": "carto-sql-test-instance",
            "project": "test-project",
        },
    ],
}

MOCK_USERS = {
    "items": [
        {
            "name": "carto-user-1",
            "host": "%",
            "instance": "carto-sql-test-instance",
            "project": "test-project",
        },
        {
            "name": "postgres",
            "host": "cloudsqlproxy~%",
            "instance": "carto-sql-test-instance",
            "project": "test-project",
        },
    ],
}
