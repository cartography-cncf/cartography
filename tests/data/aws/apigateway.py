import json
from datetime import datetime

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
        "createdDate": datetime(2021, 1, 1),
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
        "createdDate": datetime(2021, 2, 1),
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
        "createdDate": datetime(2021, 1, 1),
        "lastUpdatedDate": datetime(2021, 2, 1),
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
        "createdDate": datetime(2021, 1, 1),
        "lastUpdatedDate": datetime(2021, 2, 1),
    },
]

GET_CERTIFICATES = [
    {
        "clientCertificateId": "cert-001",
        "description": "Protection",
        "createdDate": datetime(2021, 2, 1),
        "expirationDate": datetime(2021, 4, 1),
        "stageName": "Cartography-testing-infra",
        "apiId": "test-001",
        "stageArn": "arn:aws:apigateway:::test-001/Cartography-testing-infra",
    },
    {
        "clientCertificateId": "cert-002",
        "description": "Protection",
        "createdDate": datetime(2021, 2, 1),
        "expirationDate": datetime(2021, 4, 1),
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

GET_METHODS = [
    {
        "authorizationType": "NONE",
        "apiKeyRequired": False,
        "requestParameters": {"method.request.querystring.page": False},
        "methodResponses": {"200": {"statusCode": "200"}},
        "resourceId": "3kzxbg5sa2",
        "apiId": "test-001",
        "httpMethod": "GET",
    },
]

GET_INTEGRATIONS = [
    {
        "type": "MOCK",
        "uri": "arn:aws:apigateway:us-east-1:mock",
        "resourceId": "3kzxbg5sa2",
        "apiId": "test-001",
        "httpMethod": "GET",
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
        [GET_METHODS[0]],
        [GET_INTEGRATIONS[0]],
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
        [],
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


GET_REST_API_DEPLOYMENTS = [
    {
        "id": "dep1",
        "api_id": "test-001",
        "description": "Initial deployment for v1 of the API",
        "createdDate": datetime(2023, 5, 10),
        "apiSummary": {
            "/users": {
                "GET": {"authorizationType": "NONE", "apiKeyRequired": False},
                "POST": {"authorizationType": "AWS_IAM", "apiKeyRequired": True},
            }
        },
    },
    {
        "id": "dep2",
        "api_id": "test-002",
        "description": "Deployment for v2 with additional endpoints",
        "createdDate": datetime(2024, 2, 15),
        "apiSummary": {
            "/products": {
                "GET": {"authorizationType": "NONE", "apiKeyRequired": False}
            },
            "/orders": {
                "POST": {"authorizationType": "CUSTOM", "apiKeyRequired": True}
            },
        },
    },
]
