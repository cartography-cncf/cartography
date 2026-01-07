MOCK_INSTANCES = {
    "items": [
        {
            "selfLink": "https://sqladmin.googleapis.com/sql/v1beta4/projects/test-project/instances/carto-sql-test-instance",
            "name": "carto-sql-test-instance",
            "connectionName": "test-project:us-central1:carto-sql-test-instance",
            "databaseVersion": "POSTGRES_15",
            "region": "us-central1",
            "gceZone": "us-central1-a",
            "state": "RUNNABLE",
            "backendType": "SECOND_GEN",
            "ipAddresses": [
                {"type": "PRIMARY", "ipAddress": "35.192.0.1"},
                {"type": "PRIVATE", "ipAddress": "10.0.0.5"},
            ],
            "settings": {
                "tier": "db-custom-2-7680",
                "dataDiskSizeGb": "100",
                "dataDiskType": "PD_SSD",
                "availabilityType": "REGIONAL",
                "backupConfiguration": {
                    "enabled": True,
                    "startTime": "03:00",
                    "pointInTimeRecoveryEnabled": True,
                    "transactionLogRetentionDays": 7,
                    "backupRetentionSettings": {
                        "retainedBackups": 30,
                    },
                },
                "ipConfiguration": {
                    "privateNetwork": "/projects/test-project/global/networks/carto-sql-vpc",
                    "requireSsl": True,
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
