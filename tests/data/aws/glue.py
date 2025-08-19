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

GET_GLUE_JOBS_LIST = [
    {
        "Name": "sample-etl-job",
        "CreatedOn": "2025-08-01T10:30:00",
        "LastModifiedOn": "2025-08-05T14:15:00",
        "GlueVersion": "3.0",
        "Command": {
            "Name": "glueetl",
            "ScriptLocation": "s3://my-glue-scripts/sample-etl-script.py",
            "PythonVersion": "3",
        },
        "DefaultArguments": {
            "--job-language": "python",
            "--TempDir": "s3://my-temp-bucket/temp-dir/",
        },
        "MaxCapacity": 10.0,
        "WorkerType": "G.1X",
        "NumberOfWorkers": 5,
        "ExecutionProperty": {"MaxConcurrentRuns": 2},
        "Timeout": 2880,
        "MaxRetries": 1,
        "Description": "ETL job for processing sales data",
        "Connections": {"Connections": ["test-jdbc-connection"]},
    },
    {
        "Name": "sample-streaming-job",
        "CreatedOn": "2025-08-02T09:00:00",
        "LastModifiedOn": "2025-08-06T12:45:00",
        "GlueVersion": "4.0",
        "Command": {
            "Name": "gluestreaming",
            "ScriptLocation": "s3://my-glue-scripts/sample-streaming-script.py",
            "PythonVersion": "3",
        },
        "DefaultArguments": {
            "--job-language": "python",
            "--TempDir": "s3://my-temp-bucket/temp-dir/",
        },
        "WorkerType": "G.025X",
        "NumberOfWorkers": 2,
        "ExecutionProperty": {"MaxConcurrentRuns": 1},
        "Timeout": 1440,
        "MaxRetries": 0,
        "Description": "Streaming ETL job for processing real-time events",
    },
]
