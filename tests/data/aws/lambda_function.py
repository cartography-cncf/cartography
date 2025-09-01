LIST_LAMBDA_FUNCTIONS = [
    {
        "FunctionName": "sample-function-1",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-1",
        "Runtime": "python3.7",
        "Role": "arn:aws:iam::000000000000:role/sample-role",
        "Handler": "index.lambda_handler",
        "CodeSize": 2505728,
        "Description": "",
        "Timeout": 303,
        "MemorySize": 512,
        "LastModified": "2020-03-19T23:29:12.214+0000",
        "CodeSha256": "FzVeOp307aoidqMsw=",
        "Version": "$LATEST",
        "VpcConfig": {
            "SubnetIds": [],
            "SecurityGroupIds": [],
            "VpcId": "",
        },
        "Environment": {
            "Variables": {
                "db_region": "us-west-2",
                "centralized_account_id": "000000000000",
                "region": "us-west-2",
            },
        },
        "TracingConfig": {
            "Mode": "PassThrough",
        },
        "RevisionId": "fd372ff7-0dd2-407c-b633-0a21d7ef7e53",
    },
    {
        "FunctionName": "sample-function-2",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-2",
        "Runtime": "nodejs8.10",
        "Role": "arn:aws:iam::000000000000:role/service-role/sample-role",
        "Handler": "index.handler",
        "CodeSize": 2741,
        "Description": "Sample Description",
        "Timeout": 10,
        "MemorySize": 512,
        "LastModified": "2019-10-17T22:58:32.279+0000",
        "CodeSha256": "n6sdSjaDTRrps3K9s=",
        "Version": "$LATEST",
        "VpcConfig": {
            "SubnetIds": [],
            "SecurityGroupIds": [],
            "VpcId": "",
        },
        "Environment": {
            "Variables": {
                "db_region": "us-west-2",
                "centralized_account_id": "000000000000",
                "region": "us-west-2",
            },
        },
        "TracingConfig": {
            "Mode": "PassThrough",
        },
        "RevisionId": "57f403c6-e199-4dda-8905-6108f36f4798",
        "Layers": [
            {
                "Arn": "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-1",
                "CodeSize": 123,
            }
        ],
    },
    {
        "FunctionName": "sample-function-3",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3",
        "Runtime": "dotnetcore2.1",
        "Role": "arn:aws:iam::000000000000:role/Lambda-Testing-Role",
        "Handler": "Security.Encryption.Check::Security.Encryption.Check.Lambda.Checker::GetUnEncryptedResources",
        "CodeSize": 1794723,
        "Description": "",
        "Timeout": 60,
        "MemorySize": 256,
        "LastModified": "2019-06-26T22:40:01.661+0000",
        "CodeSha256": "BRxofwyh7tLd7xkNU=",
        "Version": "$LATEST",
        "Environment": {
            "Variables": {
                "db_region": "us-west-2",
                "centralized_account_id": "000000000000",
                "region": "us-west-2",
            },
        },
        "TracingConfig": {
            "Mode": "PassThrough",
        },
        "RevisionId": "43b3eaa2-96a4-4070-a6b1-e7a2020d61f5",
        "Layers": [
            {
                "Arn": "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-2",
                "CodeSize": 123,
            }
        ],
    },
    {
        "FunctionName": "sample-function-4",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-4",
        "Runtime": "python3.7",
        "Role": "arn:aws:iam::000000000000:role/sample-role",
        "Handler": "lambda_function.lambda_handler",
        "CodeSize": 1375976,
        "Description": "",
        "Timeout": 123,
        "MemorySize": 256,
        "LastModified": "2019-09-11T20:03:29.401+0000",
        "CodeSha256": "Qz6DbhdO1ilUt+AYg=",
        "Version": "$LATEST",
        "VpcConfig": {
            "SubnetIds": [],
            "SecurityGroupIds": [],
            "VpcId": "",
        },
        "Environment": {
            "Variables": {
                "FLASHREGIONS": "us-east-1,us-west-1,us-west-2",
                "MAXRESP": "5",
            },
        },
        "TracingConfig": {
            "Mode": "PassThrough",
        },
        "RevisionId": "5e56c7d0-6f2c-4343-b511-19fda4aa2a4d",
        "Layers": [
            {
                "Arn": "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-3",
                "CodeSize": 123,
            }
        ],
    },
    {
        "FunctionName": "sample-function-5",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-5",
        "Runtime": "dotnetcore2.1",
        "Role": "arn:aws:iam::000000000000:role/Lambda-Testing-Role",
        "Handler": "Security.Encryption.Check::Security.Encryption.Check.Lambda.Checker::GetUnEncryptedResources",
        "CodeSize": 1794723,
        "Description": "",
        "Timeout": 60,
        "MemorySize": 256,
        "LastModified": "2019-06-26T22:40:02.635+0000",
        "CodeSha256": "BRxofwyh7tLd7xkNU=",
        "Version": "$LATEST",
        "Environment": {
            "Variables": {
                "TopicName": "InfoSecAlerts",
            },
        },
        "TracingConfig": {
            "Mode": "PassThrough",
        },
        "RevisionId": "aba67a63-c1cb-48a6-bc76-45a766fea64a",
    },
    {
        "FunctionName": "sample-function-6",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-6",
        "Runtime": "python3.7",
        "Role": "arn:aws:iam::000000000000:role/sample-role",
        "Handler": "index.lambda_handler",
        "CodeSize": 2507599,
        "Description": "",
        "Timeout": 243,
        "MemorySize": 512,
        "LastModified": "2020-06-04T22:06:56.809+0000",
        "CodeSha256": "SrngVRDZvPJprOMBI=",
        "Version": "$LATEST",
        "VpcConfig": {
            "SubnetIds": [],
            "SecurityGroupIds": [],
            "VpcId": "",
        },
        "Environment": {
            "Variables": {
                "db_region": "us-west-2",
                "centralized_account_id": "000000000000",
                "region": "us-west-2",
            },
        },
        "TracingConfig": {
            "Mode": "PassThrough",
        },
        "RevisionId": "df0eeb47-c36f-47c9-a719-d91281bc5f77",
    },
    {
        "FunctionName": "sample-function-7",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-7",
        "Runtime": "python3.7",
        "Role": "arn:aws:iam::000000000000:role/sample-role-2",
        "Handler": "lambda_function.lambda_handler",
        "CodeSize": 1384,
        "Description": "",
        "Timeout": 3,
        "MemorySize": 128,
        "LastModified": "2019-09-10T21:34:41.771+0000",
        "CodeSha256": "vLyig9kQUFVd3LYF0=",
        "Version": "$LATEST",
        "TracingConfig": {
            "Mode": "PassThrough",
        },
        "RevisionId": "db0ef899-cd5a-4e59-875b-4beaa5832014",
    },
    {
        "FunctionName": "sample-function-8",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-8",
        "Runtime": "python3.7",
        "Role": "arn:aws:iam::000000000000:role/sample-role",
        "Handler": "index.lambda_handler",
        "CodeSize": 2504923,
        "Description": "",
        "Timeout": 50,
        "MemorySize": 512,
        "LastModified": "2020-04-28T23:05:38.515+0000",
        "CodeSha256": "nGLwHlcDQJyxNUdQI=",
        "Version": "$LATEST",
        "VpcConfig": {
            "SubnetIds": [],
            "SecurityGroupIds": [],
            "VpcId": "",
        },
        "Environment": {
            "Variables": {
                "db_region": "us-west-2",
                "centralized_account_id": "000000000000",
                "region": "us-west-2",
            },
        },
        "TracingConfig": {
            "Mode": "PassThrough",
        },
        "RevisionId": "08c8995d-2cdc-482b-9ed4-8f9164955934",
    },
    {
        "FunctionName": "sample-function-9",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9",
        "Runtime": "python3.7",
        "Role": "arn:aws:iam::000000000000:role/sample-role-3",
        "Handler": "index.lambda_handler",
        "CodeSize": 6876,
        "Description": "",
        "Timeout": 130,
        "MemorySize": 128,
        "LastModified": "2020-03-19T20:48:43.643+0000",
        "CodeSha256": "xjEyN9xD/njVysWRA=",
        "Version": "$LATEST",
        "VpcConfig": {
            "SubnetIds": [],
            "SecurityGroupIds": [],
            "VpcId": "",
        },
        "Environment": {
            "Variables": {
                "db_region": "us-west-2",
                "centralized_account_id": "000000000000",
                "region": "us-west-2",
            },
        },
        "TracingConfig": {
            "Mode": "PassThrough",
        },
        "RevisionId": "7d2e5d1a-95cf-4a04-8936-5bed46c5a88b",
    },
    {
        "FunctionName": "sample-function-10",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10",
        "Runtime": "python3.7",
        "Role": "arn:aws:iam::000000000000:role/sample-role-4",
        "Handler": "index.lambda_handler",
        "CodeSize": 2516891,
        "Description": "",
        "Timeout": 123,
        "MemorySize": 192,
        "LastModified": "2020-03-19T23:34:16.591+0000",
        "CodeSha256": "sfkBaY2yAkEmfCMjw=",
        "Version": "$LATEST",
        "VpcConfig": {
            "SubnetIds": [],
            "SecurityGroupIds": [],
            "VpcId": "",
        },
        "Environment": {
            "Variables": {
                "db_region": "us-west-2",
                "centralized_account_id": "000000000000",
                "region": "us-west-2",
            },
        },
        "TracingConfig": {
            "Mode": "PassThrough",
        },
        "RevisionId": "8d44bdbc-9c39-4309-af5c-7d0f31fed90b",
    },
]

LIST_LAMBDA_FUNCTION_ALIASES = [
    {
        "AliasArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3:LIVE",
        "Name": "alias-1",
        "FunctionVersion": "$LATEST",
        "Description": "",
        "RevisionId": "43b3eaa2-96a4-4070-a6b1-e7a2020d61f5",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3",
    },
    {
        "AliasArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9:LIVE",
        "Name": "alias-2",
        "FunctionVersion": "$LATEST",
        "Description": "",
        "RevisionId": "7d2e5d1a-95cf-4a04-8936-5bed46c5a88b",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9",
    },
    {
        "AliasArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10:LIVE",
        "Name": "alias-3",
        "FunctionVersion": "$LATEST",
        "Description": "",
        "RevisionId": "7d2e5d1a-95cf-4a04-8936-5bed46c5a88b",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10",
    },
]

LIST_EVENT_SOURCE_MAPPINGS = [
    {
        "UUID": "i01",
        "StartingPosition": "LATEST",
        "BatchSize": 123,
        "MaximumBatchingWindowInSeconds": 123,
        "ParallelizationFactor": 123,
        "EventSourceArn": "arn:aws:sqs:us-west-2:123456789012:mySQSqueue",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-7",
        "MaximumRecordAgeInSeconds": 123,
        "BisectBatchOnFunctionError": True,
        "MaximumRetryAttempts": 123,
        "TumblingWindowInSeconds": 123,
    },
    {
        "UUID": "i02",
        "StartingPosition": "LATEST",
        "BatchSize": 123,
        "MaximumBatchingWindowInSeconds": 123,
        "ParallelizationFactor": 123,
        "EventSourceArn": "arn:aws:sqs:us-west-2:123456789012:mySQSqueue",
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-8",
        "MaximumRecordAgeInSeconds": 123,
        "BisectBatchOnFunctionError": True,
        "MaximumRetryAttempts": 123,
        "TumblingWindowInSeconds": 123,
    },
]

LIST_LAYERS = [
    {
        "Arn": "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-1",
        "CodeSize": 123,
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-2",
    },
    {
        "Arn": "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-2",
        "CodeSize": 123,
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3",
    },
    {
        "Arn": "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-3",
        "CodeSize": 123,
        "FunctionArn": "arn:aws:lambda:us-west-2:000000000000:function:sample-function-4",
    },
]

LIST_LAMBDA_PERMISSIONS = {
    "arn:aws:lambda:us-west-2:000000000000:function:sample-function-1": {
        "AnonymousAccess": False,
        "AnonymousActions": (),
    },
    "arn:aws:lambda:us-west-2:000000000000:function:sample-function-2": {
        "AnonymousAccess": True,
        "AnonymousActions": ("lambda:InvokeFunction"),
    },
    "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3": {
        "AnonymousAccess": None,
        "AnonymousActions": None,
    },
    "arn:aws:lambda:us-west-2:000000000000:function:sample-function-4": {
        "AnonymousAccess": None,
        "AnonymousActions": None,
    },
    "arn:aws:lambda:us-west-2:000000000000:function:sample-function-5": {
        "AnonymousAccess": None,
        "AnonymousActions": None,
    },
    "arn:aws:lambda:us-west-2:000000000000:function:sample-function-6": {
        "AnonymousAccess": None,
        "AnonymousActions": None,
    },
    "arn:aws:lambda:us-west-2:000000000000:function:sample-function-7": {
        "AnonymousAccess": None,
        "AnonymousActions": None,
    },
    "arn:aws:lambda:us-west-2:000000000000:function:sample-function-8": {
        "AnonymousAccess": None,
        "AnonymousActions": None,
    },
    "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9": {
        "AnonymousAccess": None,
        "AnonymousActions": None,
    },
    "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10": {
        "AnonymousAccess": None,
        "AnonymousActions": None,
    },
}


# Mock functions for comprehensive sync test
def mock_get_function_aliases_for_sync_test(lambda_function, client):
    """Return aliases only for functions that have them"""
    all_aliases = LIST_LAMBDA_FUNCTION_ALIASES

    # Return only aliases that belong to this specific function
    function_aliases = []
    for alias in all_aliases:
        if alias["FunctionArn"] == lambda_function["FunctionArn"]:
            function_aliases.append(alias)

    return function_aliases


def mock_get_event_source_mappings_for_sync_test(lambda_function, client):
    """Return event source mappings only for functions that have them"""
    all_mappings = LIST_EVENT_SOURCE_MAPPINGS

    # Return only mappings that belong to this specific function
    function_mappings = []
    for mapping in all_mappings:
        if mapping["FunctionArn"] == lambda_function["FunctionArn"]:
            function_mappings.append(mapping)

    return function_mappings
