import datetime

LIST_DYNAMODB_TABLES = {
    "Tables": [
        {
            "Table": {
                "TableArn": "arn:aws:dynamodb:us-east-1:000000000000:table/example-table",
                "AttributeDefinitions": [
                    {
                        "AttributeName": "sample_1",
                        "AttributeType": "A",
                    },
                    {
                        "AttributeName": "sample_2",
                        "AttributeType": "B",
                    },
                    {
                        "AttributeName": "sample_3",
                        "AttributeType": "C",
                    },
                ],
                "GlobalSecondaryIndexes": [
                    {
                        "IndexSizeBytes": 11111111,
                        "IndexName": "sample_index_1",
                        "Projection": {
                            "ProjectionType": "ALL",
                        },
                        "ProvisionedThroughput": {
                            "WriteCapacityUnits": 30,
                            "ReadCapacityUnits": 30,
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema",
                            },
                        ],
                        "IndexArn": "arn:aws:dynamodb:us-east-1:table/example-table/index/sample_1-index",
                        "ItemCount": 1000000,
                    },
                    {
                        "IndexSizeBytes": 22222222,
                        "IndexName": "sample_index_2",
                        "Projection": {
                            "ProjectionType": "ALL",
                        },
                        "ProvisionedThroughput": {
                            "WriteCapacityUnits": 40,
                            "ReadCapacityUnits": 40,
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema",
                            },
                        ],
                        "IndexArn": "arn:aws:dynamodb:us-east-1:table/example-table/index/sample_2-index",
                        "ItemCount": 1000000,
                    },
                ],
                "ProvisionedThroughput": {
                    "NumberOfDecreasesToday": 10,
                    "WriteCapacityUnits": 10,
                    "LastIncreaseDateTime": datetime.datetime(2019, 1, 1, 0, 0, 1),
                    "ReadCapacityUnits": 10,
                    "LastDecreaseDateTime": datetime.datetime(2019, 1, 1, 0, 0, 1),
                },
                "TableSizeBytes": 100000000,
                "TableName": "example-table",
                "TableStatus": "ACTIVE",
                "StreamSpecification": {
                    "StreamViewType": "SAMPLE_STREAM_VIEW_TYPE",
                    "StreamEnabled": True,
                },
                "TableId": "00000000-0000-0000-0000-000000000000",
                "LatestStreamLabel": "0000-00-00000:00:00.000",
                "KeySchema": [
                    {
                        "KeyType": "HASH",
                        "AttributeName": "sample_schema",
                    },
                ],
                "ItemCount": 1000000,
                "CreationDateTime": datetime.datetime(2019, 1, 1, 0, 0, 1),
                "LatestStreamArn": "arn:aws:dynamodb:us-east-1:table/example-table/stream/0000-00-00000:00:00.000",
                "BillingModeSummary": {
                    "BillingMode": "PROVISIONED",
                    "LastUpdateToPayPerRequestDateTime": datetime.datetime(
                        2020, 6, 15, 10, 30, 0
                    ),
                },
                "SSEDescription": {
                    "Status": "ENABLED",
                    "SSEType": "KMS",
                    "KMSMasterKeyArn": "arn:aws:kms:us-east-1:000000000000:key/12345678-1234-1234-1234-123456789012",
                },
            },
        },
        {
            "Table": {
                "TableArn": "arn:aws:dynamodb:us-east-1:000000000000:table/sample-table",
                "GlobalSecondaryIndexes": [
                    {
                        "IndexSizeBytes": 11111111,
                        "IndexName": "sample_index_1",
                        "Projection": {
                            "ProjectionType": "ALL",
                        },
                        "ProvisionedThroughput": {
                            "WriteCapacityUnits": 30,
                            "ReadCapacityUnits": 30,
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema",
                            },
                        ],
                        "IndexArn": "arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_1-index",
                        "ItemCount": 1000000,
                    },
                    {
                        "IndexSizeBytes": 22222222,
                        "IndexName": "sample_index_2",
                        "Projection": {
                            "ProjectionType": "ALL",
                        },
                        "ProvisionedThroughput": {
                            "WriteCapacityUnits": 40,
                            "ReadCapacityUnits": 40,
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema",
                            },
                        ],
                        "IndexArn": "arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_2-index",
                        "ItemCount": 1000000,
                    },
                    {
                        "IndexSizeBytes": 33333333,
                        "IndexName": "sample_index_3",
                        "Projection": {
                            "ProjectionType": "ALL",
                        },
                        "ProvisionedThroughput": {
                            "WriteCapacityUnits": 50,
                            "ReadCapacityUnits": 50,
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema",
                            },
                        ],
                        "IndexArn": "arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_3-index",
                        "ItemCount": 1000000,
                    },
                ],
                "ProvisionedThroughput": {
                    "NumberOfDecreasesToday": 10,
                    "WriteCapacityUnits": 10,
                    "LastIncreaseDateTime": datetime.datetime(2019, 1, 1, 0, 0, 1),
                    "ReadCapacityUnits": 10,
                    "LastDecreaseDateTime": datetime.datetime(2019, 1, 1, 0, 0, 1),
                },
                "TableSizeBytes": 100000000,
                "TableName": "sample-table",
                "TableStatus": "ACTIVE",
                "TableId": "00000000-0000-0000-0000-000000000000",
                "LatestStreamLabel": "0000-00-00000:00:00.000",
                "ItemCount": 1000000,
                "CreationDateTime": datetime.datetime(2019, 1, 1, 0, 0, 1),
                "LatestStreamArn": "arn:aws:dynamodb:us-east-1:table/sample-table/stream/0000-00-00000:00:00.000",
                "BillingModeSummary": {
                    "BillingMode": "PAY_PER_REQUEST",
                },
            },
        },
        {
            "Table": {
                "TableArn": "arn:aws:dynamodb:us-east-1:000000000000:table/model-table",
                "GlobalSecondaryIndexes": [
                    {
                        "IndexSizeBytes": 11111111,
                        "IndexName": "sample_index_1",
                        "Projection": {
                            "ProjectionType": "ALL",
                        },
                        "ProvisionedThroughput": {
                            "WriteCapacityUnits": 30,
                            "ReadCapacityUnits": 30,
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema",
                            },
                        ],
                        "IndexArn": "arn:aws:dynamodb:us-east-1:table/model-table/index/sample_1-index",
                        "ItemCount": 1000000,
                    },
                    {
                        "IndexSizeBytes": 22222222,
                        "IndexName": "sample_index_2",
                        "Projection": {
                            "ProjectionType": "ALL",
                        },
                        "ProvisionedThroughput": {
                            "WriteCapacityUnits": 40,
                            "ReadCapacityUnits": 40,
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema",
                            },
                        ],
                        "IndexArn": "arn:aws:dynamodb:us-east-1:table/model-table/index/sample_2-index",
                        "ItemCount": 1000000,
                    },
                    {
                        "IndexSizeBytes": 33333333,
                        "IndexName": "sample_index_3",
                        "Projection": {
                            "ProjectionType": "ALL",
                        },
                        "ProvisionedThroughput": {
                            "WriteCapacityUnits": 50,
                            "ReadCapacityUnits": 50,
                        },
                        "IndexStatus": "ACTIVE",
                        "KeySchema": [
                            {
                                "KeyType": "HASH",
                                "AttributeName": "sample_schema",
                            },
                        ],
                        "IndexArn": "arn:aws:dynamodb:us-east-1:table/model-table/index/sample_3-index",
                        "ItemCount": 1000000,
                    },
                ],
                "ProvisionedThroughput": {
                    "NumberOfDecreasesToday": 10,
                    "WriteCapacityUnits": 10,
                    "LastIncreaseDateTime": datetime.datetime(2019, 1, 1, 0, 0, 1),
                    "ReadCapacityUnits": 10,
                    "LastDecreaseDateTime": datetime.datetime(2019, 1, 1, 0, 0, 1),
                },
                "TableSizeBytes": 100000000,
                "TableName": "model-table",
                "TableStatus": "ACTIVE",
                "TableId": "00000000-0000-0000-0000-000000000000",
                "LatestStreamLabel": "0000-00-00000:00:00.000",
                "ItemCount": 1000000,
                "CreationDateTime": datetime.datetime(2019, 1, 1, 0, 0, 1),
                "LatestStreamArn": "arn:aws:dynamodb:us-east-1:table/model-table/stream/0000-00-00000:00:00.000",
                "StreamSpecification": {
                    "StreamViewType": "NEW_AND_OLD_IMAGES",
                    "StreamEnabled": True,
                },
                "RestoreSummary": {
                    "RestoreDateTime": datetime.datetime(2021, 3, 10, 14, 25, 0),
                    "RestoreInProgress": False,
                    "SourceBackupArn": "arn:aws:dynamodb:us-east-1:000000000000:table/model-table/backup/01234567890123-abcdefgh",
                    "SourceTableArn": "arn:aws:dynamodb:us-east-1:000000000000:table/original-model-table",
                },
            },
        },
        {
            "Table": {
                "TableArn": "arn:aws:dynamodb:us-east-1:000000000000:table/basic-table",
                "ProvisionedThroughput": {
                    "NumberOfDecreasesToday": 10,
                    "WriteCapacityUnits": 10,
                    "LastIncreaseDateTime": datetime.datetime(2019, 1, 1, 0, 0, 1),
                    "ReadCapacityUnits": 10,
                    "LastDecreaseDateTime": datetime.datetime(2019, 1, 1, 0, 0, 1),
                },
                "TableSizeBytes": 100000000,
                "TableName": "basic-table",
                "TableStatus": "ACTIVE",
                "TableId": "00000000-0000-0000-0000-000000000000",
                "LatestStreamLabel": "0000-00-00000:00:00.000",
                "ItemCount": 1000000,
                "CreationDateTime": datetime.datetime(2019, 1, 1, 0, 0, 1),
                "LatestStreamArn": "arn:aws:dynamodb:us-east-1:table/basic-table/stream/0000-00-00000:00:00.000",
            },
        },
        {
            "Table": {
                "TableArn": "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table",
                "ProvisionedThroughput": {
                    "NumberOfDecreasesToday": 5,
                    "WriteCapacityUnits": 5,
                    "LastIncreaseDateTime": datetime.datetime(2018, 6, 1, 0, 0, 1),
                    "ReadCapacityUnits": 5,
                    "LastDecreaseDateTime": datetime.datetime(2018, 6, 1, 0, 0, 1),
                },
                "TableSizeBytes": 50000000,
                "TableName": "archived-table",
                "TableStatus": "ARCHIVED",
                "TableId": "11111111-1111-1111-1111-111111111111",
                "ItemCount": 500000,
                "CreationDateTime": datetime.datetime(2018, 1, 1, 0, 0, 1),
                "ArchivalSummary": {
                    "ArchivalDateTime": datetime.datetime(2022, 8, 20, 9, 15, 0),
                    "ArchivalReason": "Manual archival by administrator",
                    "ArchivalBackupArn": "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table/backup/archived-backup-123",
                },
                "BillingModeSummary": {
                    "BillingMode": "PROVISIONED",
                },
            },
        },
        {
            "Table": {
                "TableArn": "arn:aws:dynamodb:us-east-1:000000000000:table/encrypted-table",
                "ProvisionedThroughput": {
                    "NumberOfDecreasesToday": 0,
                    "WriteCapacityUnits": 25,
                    "LastIncreaseDateTime": datetime.datetime(2020, 10, 15, 0, 0, 1),
                    "ReadCapacityUnits": 25,
                    "LastDecreaseDateTime": datetime.datetime(2020, 10, 15, 0, 0, 1),
                },
                "TableSizeBytes": 75000000,
                "TableName": "encrypted-table",
                "TableStatus": "ACTIVE",
                "TableId": "22222222-2222-2222-2222-222222222222",
                "ItemCount": 750000,
                "CreationDateTime": datetime.datetime(2020, 10, 1, 0, 0, 1),
                "SSEDescription": {
                    "Status": "ENABLED",
                    "SSEType": "KMS",
                    "KMSMasterKeyArn": "arn:aws:kms:us-east-1:000000000000:key/87654321-4321-4321-4321-210987654321",
                },
                "BillingModeSummary": {
                    "BillingMode": "PROVISIONED",
                    "LastUpdateToPayPerRequestDateTime": datetime.datetime(
                        2021, 2, 10, 16, 45, 30
                    ),
                },
                "StreamSpecification": {
                    "StreamViewType": "KEYS_ONLY",
                    "StreamEnabled": True,
                },
                "LatestStreamArn": "arn:aws:dynamodb:us-east-1:table/encrypted-table/stream/2021-02-10T16:45:30.000",
                "LatestStreamLabel": "2021-02-10T16:45:30.000",
            },
        },
        {
            "Table": {
                "TableArn": "arn:aws:dynamodb:us-east-1:000000000000:table/restored-table",
                "ProvisionedThroughput": {
                    "NumberOfDecreasesToday": 2,
                    "WriteCapacityUnits": 15,
                    "LastIncreaseDateTime": datetime.datetime(2021, 5, 20, 0, 0, 1),
                    "ReadCapacityUnits": 15,
                    "LastDecreaseDateTime": datetime.datetime(2021, 5, 20, 0, 0, 1),
                },
                "TableSizeBytes": 60000000,
                "TableName": "restored-table",
                "TableStatus": "ACTIVE",
                "TableId": "33333333-3333-3333-3333-333333333333",
                "ItemCount": 600000,
                "CreationDateTime": datetime.datetime(2021, 5, 1, 0, 0, 1),
                "RestoreSummary": {
                    "RestoreDateTime": datetime.datetime(2021, 5, 15, 10, 30, 0),
                    "RestoreInProgress": True,
                    "SourceBackupArn": "arn:aws:dynamodb:us-east-1:000000000000:table/source-table/backup/backup-456",
                    "SourceTableArn": "arn:aws:dynamodb:us-east-1:000000000000:table/source-table",
                },
                "BillingModeSummary": {
                    "BillingMode": "PAY_PER_REQUEST",
                },
                "SSEDescription": {
                    "Status": "ENABLED",
                    "SSEType": "AES256",
                },
            },
        },
    ],
}
