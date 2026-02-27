MOCK_DATASETS = {
    "datasets": [
        {
            "datasetReference": {
                "projectId": "test-project",
                "datasetId": "my_dataset",
            },
            "friendlyName": "My Dataset",
            "description": "A test dataset",
            "location": "US",
            "creationTime": "1640000000000",
            "lastModifiedTime": "1640100000000",
            "defaultTableExpirationMs": "86400000",
            "defaultPartitionExpirationMs": None,
        },
        {
            "datasetReference": {
                "projectId": "test-project",
                "datasetId": "other_dataset",
            },
            "friendlyName": "Other Dataset",
            "description": None,
            "location": "EU",
            "creationTime": "1640200000000",
            "lastModifiedTime": "1640300000000",
            "defaultTableExpirationMs": None,
            "defaultPartitionExpirationMs": None,
        },
    ],
}

MOCK_TABLES_MY_DATASET = {
    "tables": [
        {
            "tableReference": {
                "projectId": "test-project",
                "datasetId": "my_dataset",
                "tableId": "users",
            },
            "type": "TABLE",
            "creationTime": "1640000000000",
            "expirationTime": None,
        },
        {
            "tableReference": {
                "projectId": "test-project",
                "datasetId": "my_dataset",
                "tableId": "user_view",
            },
            "type": "VIEW",
            "creationTime": "1640050000000",
            "expirationTime": None,
        },
    ],
}

MOCK_TABLES_OTHER_DATASET = {
    "tables": [
        {
            "tableReference": {
                "projectId": "test-project",
                "datasetId": "other_dataset",
                "tableId": "events",
            },
            "type": "TABLE",
            "creationTime": "1640200000000",
            "expirationTime": "1672000000000",
        },
    ],
}

# tables.get responses — these contain the full table resource with fields
# not present in tables.list (numBytes, numRows, description, externalDataConfiguration, etc.)
MOCK_TABLE_DETAIL_USERS = {
    "tableReference": {
        "projectId": "test-project",
        "datasetId": "my_dataset",
        "tableId": "users",
    },
    "type": "TABLE",
    "creationTime": "1640000000000",
    "expirationTime": None,
    "numBytes": "1024",
    "numLongTermBytes": "512",
    "numRows": "100",
    "description": "User accounts table",
    "friendlyName": "Users",
}

MOCK_TABLE_DETAIL_USER_VIEW = {
    "tableReference": {
        "projectId": "test-project",
        "datasetId": "my_dataset",
        "tableId": "user_view",
    },
    "type": "VIEW",
    "creationTime": "1640050000000",
    "expirationTime": None,
    "numBytes": None,
    "numLongTermBytes": None,
    "numRows": None,
    "description": "View over users table",
    "friendlyName": "User View",
}

MOCK_TABLE_DETAIL_EVENTS = {
    "tableReference": {
        "projectId": "test-project",
        "datasetId": "other_dataset",
        "tableId": "events",
    },
    "type": "TABLE",
    "creationTime": "1640200000000",
    "expirationTime": "1672000000000",
    "numBytes": "2048",
    "numLongTermBytes": "0",
    "numRows": "500",
    "description": "Event log table",
    "friendlyName": "Events",
    "externalDataConfiguration": {
        "connectionId": "projects/test-project/locations/us/connections/my-cloud-sql-conn",
        "sourceFormat": "MYSQL",
    },
}

MOCK_ROUTINES_MY_DATASET = {
    "routines": [
        {
            "routineReference": {
                "projectId": "test-project",
                "datasetId": "my_dataset",
                "routineId": "my_udf",
            },
            "routineType": "SCALAR_FUNCTION",
            "language": "SQL",
            "creationTime": "1640000000000",
            "lastModifiedTime": "1640100000000",
        },
        {
            "routineReference": {
                "projectId": "test-project",
                "datasetId": "my_dataset",
                "routineId": "my_remote_fn",
            },
            "routineType": "SCALAR_FUNCTION",
            "language": "PYTHON",
            "creationTime": "1640000000000",
            "lastModifiedTime": "1640100000000",
            "remoteFunctionOptions": {
                "connection": "projects/test-project/locations/us/connections/my-spark-conn",
                "endpoint": "https://my-endpoint.run.app",
            },
        },
    ],
}

MOCK_ROUTINES_OTHER_DATASET: dict[str, list] = {
    "routines": [],
}

MOCK_CONNECTIONS = {
    "connections": [
        {
            "name": "projects/test-project/locations/us/connections/my-cloud-sql-conn",
            "friendlyName": "My Cloud SQL Connection",
            "description": "Connection to Cloud SQL",
            "creationTime": "1640000000000",
            "lastModifiedTime": "1640100000000",
            "hasCredential": True,
            "cloudSql": {
                "instanceId": "test-project:us-central1:my-instance",
                "database": "mydb",
                "type": "MYSQL",
            },
        },
        {
            "name": "projects/test-project/locations/us/connections/my-spark-conn",
            "friendlyName": "My Spark Connection",
            "description": None,
            "creationTime": "1640200000000",
            "lastModifiedTime": "1640300000000",
            "hasCredential": False,
            "spark": {},
        },
    ],
}
