GET_GLUE_CONNECTIONS_LIST = [
    {
        "Name": "test-jdbc-connection",
        "Description": "Test JDBC connection to MySQL instance",
        "ConnectionType": "JDBC",
        "MatchCriteria": ["test", "mysql"],
        "ConnectionProperties": {
            "USERNAME": "test_user",
            "PASSWORD": "test_pass",
            "JDBC_CONNECTION_URL": "jdbc:mysql://db.example.com:3306/testdb",
            "JDBC_ENFORCE_SSL": "false",
        },
        "SparkProperties": {"spark.sql.shuffle.partitions": "10"},
        "AthenaProperties": {},
        "PythonProperties": {},
        "PhysicalConnectionRequirements": {
            "SubnetId": "subnet-1234abcd",
            "SecurityGroupIdList": ["sg-0123abcd"],
            "AvailabilityZone": "us-east-1a",
        },
        "CreationTime": "2023-08-01T10:00:00Z",
        "LastUpdatedTime": "2023-08-15T12:00:00Z",
        "LastUpdatedBy": "arn:aws:iam::123456789012:user/dev-user",
        "Status": "READY",
        "StatusReason": "Validated successfully",
        "LastConnectionValidationTime": "2023-08-15T12:00:00Z",
        "AuthenticationConfiguration": {
            "AuthenticationType": "BASIC",
            "SecretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:mysql-credentials-abc123",
        },
        "ConnectionSchemaVersion": 1,
        "CompatibleComputeEnvironments": ["SPARK", "PYTHON"],
    }
]
