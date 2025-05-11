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
                        "IndexName": "sample_index_2",
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
                        "IndexName": "sample_index_2",
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
    ],
}
