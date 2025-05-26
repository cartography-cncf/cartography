import datetime
import json

DOUBLY_ESCAPED_POLICY = (
    """{\\\"Version\\\":\\\"2012-10-17\\\","""
    + """\\\"Statement\\\":[{\\\"Effect\\\":\\\"Allow\\\","""
    + """\\\"Principal\\\":\\\"*\\\",\\\"Action\\\":\\\"execute-api:Invoke\\\","""
    + """\\\"Resource\\\":\\\"arn:aws:execute-api:us-east-1:deadbeef:2stva8ras3"""
    + """\\/*\\/*\\/*\\\"}]}"""
)

GET_REST_APIS = [
    {
        "id": "test-001",
        "name": "Infra-testing-cartography",
        "description": "Testing for Cartography",
        "createdDate": datetime.datetime(2021, 1, 1),
        "version": "1.0",
        "warnings": [
            "Possible Failure",
        ],
        "minimumCompressionSize": 123,
        "apiKeySource": "HEADER",
        "endpointConfiguration": {
            "types": [
                "REGIONAL",
            ],
            "vpcEndpointIds": [
                "demo-1",
            ],
        },
        "disableExecuteApiEndpoint": True,
    },
    {
        "id": "test-002",
        "name": "Unit-testing-cartography",
        "description": "Unit Testing for Cartography",
        "createdDate": datetime.datetime(2021, 2, 1),
        "version": "1.0",
        "warnings": [
            "Possible Failure",
        ],
        "minimumCompressionSize": 123,
        "apiKeySource": "HEADER",
        "endpointConfiguration": {
            "types": [
                "PRIVATE",
            ],
            "vpcEndpointIds": [
                "demo-1",
            ],
        },
        "disableExecuteApiEndpoint": False,
    },
]

GET_STAGES = [
    {
        "arn": "arn:aws:apigateway:::test-001/Cartography-testing-infra",
        "deploymentId": "d-001",
        "apiId": "test-001",
        "clientCertificateId": "cert-001",
        "stageName": "Cartography-testing-infra",
        "description": "Testing",
        "cacheClusterEnabled": True,
        "cacheClusterSize": "0.5",
        "cacheClusterStatus": "AVAILABLE",
        "methodSettings": {
            "msk-01": {
                "metricsEnabled": True,
                "loggingLevel": "OFF",
                "dataTraceEnabled": True,
                "throttlingBurstLimit": 123,
                "throttlingRateLimit": 123.0,
                "cachingEnabled": True,
                "cacheTtlInSeconds": 123,
                "cacheDataEncrypted": True,
                "requireAuthorizationForCacheControl": True,
                "unauthorizedCacheControlHeaderStrategy": "FAIL_WITH_403",
            },
        },
        "documentationVersion": "1.17.14",
        "tracingEnabled": True,
        "webAclArn": "arn:aws:wafv2:us-west-2:1234567890:regional/webacl/test-cli/a1b2c3d4-5678-90ab-cdef-EXAMPLE111",
        "createdDate": datetime.datetime(2021, 1, 1),
        "lastUpdatedDate": datetime.datetime(2021, 2, 1),
    },
    {
        "arn": "arn:aws:apigateway:::test-002/Cartography-testing-unit",
        "deploymentId": "d-002",
        "apiId": "test-002",
        "clientCertificateId": "cert-002",
        "stageName": "Cartography-testing-unit",
        "description": "Testing",
        "cacheClusterEnabled": True,
        "cacheClusterSize": "0.5",
        "cacheClusterStatus": "AVAILABLE",
        "methodSettings": {
            "msk-02": {
                "metricsEnabled": True,
                "loggingLevel": "OFF",
                "dataTraceEnabled": True,
                "throttlingBurstLimit": 123,
                "throttlingRateLimit": 123.0,
                "cachingEnabled": True,
                "cacheTtlInSeconds": 123,
                "cacheDataEncrypted": True,
                "requireAuthorizationForCacheControl": True,
                "unauthorizedCacheControlHeaderStrategy": "FAIL_WITH_403",
            },
        },
        "documentationVersion": "1.17.14",
        "tracingEnabled": True,
        "webAclArn": "arn:aws:wafv2:us-west-2:1234567890:regional/webacl/test-cli/a1b2c3d4-5678-90ab-cdef-EXAMPLE111",
        "createdDate": datetime.datetime(2021, 1, 1),
        "lastUpdatedDate": datetime.datetime(2021, 2, 1),
    },
]

GET_CERTIFICATES = [
    {
        "clientCertificateId": "cert-001",
        "description": "Protection",
        "createdDate": datetime.datetime(2021, 2, 1),
        "expirationDate": datetime.datetime(2021, 4, 1),
        "stageName": "Cartography-testing-infra",
        "apiId": "test-001",
        "stageArn": "arn:aws:apigateway:::test-001/Cartography-testing-infra",
    },
    {
        "clientCertificateId": "cert-002",
        "description": "Protection",
        "createdDate": datetime.datetime(2021, 2, 1),
        "expirationDate": datetime.datetime(2021, 4, 1),
        "stageName": "Cartography-testing-unit",
        "apiId": "test-002",
        "stageArn": "arn:aws:apigateway:::test-002/Cartography-testing-unit",
    },
]

GET_RESOURCES = [
    {
        "id": "3kzxbg5sa2",
        "apiId": "test-001",
        "parentId": "ababababab",
        "pathPart": "resource",
        "path": "/restapis/test-001/resources/3kzxbg5sa2",
    },
]

# This represents the tuple of (api_id, stage, certificate, resource, policy) that get_rest_api_details returns
GET_REST_API_DETAILS = [
    # We use json.dumps() to simulate the fact that the policy is a string,
    # see https://boto3.amazonaws.com/v1/documentation/
    # api/latest/reference/services/apigateway/client/get_rest_apis.html
    (
        "test-001",
        [GET_STAGES[0]],
        GET_CERTIFICATES[0],
        [GET_RESOURCES[0]],
        json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": ["execute-api:Invoke", "execute-api:GetApi"],
                        "Resource": "arn:aws:execute-api:us-east-1:000000000000:test-001/*",
                    },
                ],
            },
        ),
    ),
    (
        "test-002",
        [GET_STAGES[1]],
        GET_CERTIFICATES[1],
        [],
        json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "arn:aws:iam::000000000000:some-principal",
                        },
                        "Action": "execute-api:Invoke",
                        "Resource": "arn:aws:execute-api:us-east-1:000000000000:test-002/*",
                    },
                ],
            },
        ),
    ),
]

METHOD_RESPONSE_GET = {
    "authorizationType": "NONE",
    "apiKeyRequired": False,
    "operationName": "RetrieveResource",
    "methodIntegration_json": json.dumps(
        {
            "type": "AWS_PROXY",
            "httpMethod": "GET",
            "uri": "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-west-2:000000000000:function:sample-function-1/invocations",
            "passthroughBehavior": "WHEN_NO_MATCH",
            "connectionType": "INTERNET",
            "timeoutInMillis": 29000,
        }
    ),
    "methodResponses_json": json.dumps(
        {
            "200": {
                "statusCode": "200",
                "responseModels": {
                    "application/json": "Empty",
                },
                "responseParameters": {
                    "method.response.header.Access-Control-Allow-Origin": False,
                },
            },
        }
    ),
    "requestModels_json": json.dumps(
        {
            "application/json": "Empty",
        }
    ),
    "requestParameters_json": json.dumps(
        {
            "method.request.querystring.param1": False,
        }
    ),
    "requestValidatorId": "validator-id-1",
    "authorizerId": None,
    "RestApiId": "test-001",
    "ResourceId": "3kzxbg5sa2",
    "HttpMethod": "GET",
}


METHOD_RESPONSE_POST = {
    "authorizationType": "AWS_IAM",
    "apiKeyRequired": True,
    "operationName": "CreateResource",
    "methodIntegration_json": json.dumps(
        {
            "type": "AWS_PROXY",
            "httpMethod": "POST",
            "uri": "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-west-2:000000000000:function:sample-function-2/invocations",
            "passthroughBehavior": "WHEN_NO_MATCH",
            "connectionType": "INTERNET",
            "timeoutInMillis": 29000,
        }
    ),
    "methodResponses_json": json.dumps(
        {
            "200": {
                "statusCode": "200",
                "responseModels": {},
            },
        }
    ),
    "requestModels_json": json.dumps({}),
    "requestParameters_json": json.dumps({}),
    "requestValidatorId": None,
    "authorizerId": None,
    "RestApiId": "test-001",
    "ResourceId": "3kzxbg5sa2",
    "HttpMethod": "POST",
}

METHOD_RESPONSE_PUT = {
    "authorizationType": "CUSTOM",
    "authorizerId": "ab12cdefgh",
    "apiKeyRequired": False,
    "operationName": "UpdateResource",
    "methodIntegration_json": json.dumps(
        {
            "type": "MOCK",
            "httpMethod": "PUT",
            "uri": "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/",
            "passthroughBehavior": "WHEN_NO_MATCH",
        }
    ),
    "methodResponses_json": json.dumps(
        {
            "200": {
                "statusCode": "200",
            },
        }
    ),
    "requestModels_json": json.dumps({}),
    "requestParameters_json": json.dumps({}),
    "requestValidatorId": None,
    "RestApiId": "test-001",
    "ResourceId": "3kzxbg5sa2",
    "HttpMethod": "PUT",
}


METHOD_RESPONSE_S3 = {
    "authorizationType": "AWS_IAM",
    "apiKeyRequired": False,
    "operationName": "DeleteObject",
    "methodIntegration_json": json.dumps(
        {
            "type": "AWS",
            "httpMethod": "DELETE",
            "uri": "arn:aws:s3:::bucket-1/some/object",
            "passthroughBehavior": "WHEN_NO_MATCH",
            "timeoutInMillis": 29000,
        }
    ),
    "methodResponses_json": json.dumps(
        {
            "204": {
                "statusCode": "204",
            },
        }
    ),
    "requestModels_json": json.dumps({}),
    "requestParameters_json": json.dumps(
        {"integration.request.header.x-amz-acl": True}
    ),
    "requestValidatorId": None,
    "authorizerId": None,
    "RestApiId": "test-001",
    "ResourceId": "3kzxbg5sa2",
    "HttpMethod": "DELETE",
}

METHOD_RESPONSE_DDB = {
    "authorizationType": "AWS_IAM",
    "apiKeyRequired": True,
    "operationName": "UpdateItem",
    "methodIntegration_json": json.dumps(
        {
            "type": "AWS",
            "httpMethod": "POST",
            "uri": "arn:aws:dynamodb:us-east-1:000000000000:table/example-table",
            "passthroughBehavior": "WHEN_NO_MATCH",
            "timeoutInMillis": 29000,
        }
    ),
    "methodResponses_json": json.dumps(
        {
            "200": {
                "statusCode": "200",
            }
        }
    ),
    "requestModels_json": json.dumps({}),
    "requestParameters_json": json.dumps({}),
    "requestValidatorId": None,
    "authorizerId": None,
    "RestApiId": "test-001",
    "ResourceId": "3kzxbg5sa2",
    "HttpMethod": "PATCH",
}


MOCK_GET_METHOD_RESPONSES = {
    ("test-001", "3kzxbg5sa2", "GET"): METHOD_RESPONSE_GET,
    ("test-001", "3kzxbg5sa2", "POST"): METHOD_RESPONSE_POST,
    ("test-001", "3kzxbg5sa2", "PUT"): METHOD_RESPONSE_PUT,
    ("test-001", "3kzxbg5sa2", "DELETE"): METHOD_RESPONSE_S3,
    ("test-001", "3kzxbg5sa2", "PATCH"): METHOD_RESPONSE_DDB,
}
