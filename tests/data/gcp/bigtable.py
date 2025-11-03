MOCK_INSTANCES = {
    "instances": [
        {
            "name": "projects/test-project/instances/carto-bt-instance",
            "displayName": "carto-bt-instance",
            "state": "READY",
            "type": "PRODUCTION",
        },
    ],
}

MOCK_CLUSTERS = {
    "clusters": [
        {
            "name": "projects/test-project/instances/carto-bt-instance/clusters/carto-bt-cluster-c1",
            "location": "projects/test-project/locations/us-central1-b",
            "state": "READY",
            "defaultStorageType": "SSD",
        },
    ],
}

MOCK_TABLES = {
    "tables": [
        {
            "name": "projects/test-project/instances/carto-bt-instance/tables/carto-test-table",
            "granularity": "MILLIS",
        },
    ],
}

MOCK_APP_PROFILES = {
    "appProfiles": [
        {
            "name": "projects/test-project/instances/carto-bt-instance/appProfiles/carto-app-profile",
            "description": "Test profile",
            "singleClusterRouting": {
                "clusterId": "carto-bt-cluster-c1",
                "allowTransactionalWrites": True,
            },
        },
    ],
}

MOCK_BACKUPS = {
    "backups": [
        {
            "name": "projects/test-project/instances/carto-bt-instance/clusters/carto-bt-cluster-c1/backups/carto-table-backup",
            "sourceTable": "projects/test-project/instances/carto-bt-instance/tables/carto-test-table",
            "expireTime": "2025-11-10T05:00:00Z",
            "startTime": "2025-11-03T05:00:00Z",
            "endTime": "2025-11-03T05:01:00Z",
            "sizeBytes": 123456789,
            "state": "READY",
        },
    ],
}
