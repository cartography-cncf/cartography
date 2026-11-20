from datetime import datetime

GET_APIS = [
    {
        "ApiId": "api-001",
        "Name": "HTTP-Test",
        "ProtocolType": "HTTP",
        "RouteSelectionExpression": "$request.method $request.path",
        "Version": "1.0",
        "CreatedDate": datetime(2024, 1, 1),
        "ApiEndpoint": "https://api-001.execute-api.us-east-1.amazonaws.com",
        "Description": "HTTP API test",
        "ApiKeySelectionExpression": "$request.header.x-api-key",
    },
    {
        "ApiId": "api-002",
        "Name": "WS-Test",
        "ProtocolType": "WEBSOCKET",
        "RouteSelectionExpression": "$request.body.action",
        "Version": "1.0",
        "CreatedDate": datetime(2024, 1, 2),
        "ApiEndpoint": "https://api-002.execute-api.us-east-1.amazonaws.com",
        "Description": "WebSocket API test",
        "ApiKeySelectionExpression": "$request.header.x-api-key",
    },
]

# A stage of api-001 with every optional member populated.
STAGE_API_001_PROD = {
    "StageName": "prod",
    "AutoDeploy": True,
    "DeploymentId": "deployment-001",
    "Description": "Production stage",
    "CreatedDate": datetime(2024, 2, 1),
    "LastUpdatedDate": datetime(2024, 2, 2),
    "ApiGatewayManaged": True,
    "ClientCertificateId": "cert-001",
}

# A stage of api-001 missing the optional DeploymentId, Description,
# LastUpdatedDate, ApiGatewayManaged, and ClientCertificateId members.
STAGE_API_001_DEV = {
    "StageName": "dev",
    "AutoDeploy": False,
    "CreatedDate": datetime(2024, 2, 1),
}

# get_stages(ApiId="api-001").
GET_STAGES_RESPONSE_API_001 = {
    "Items": [STAGE_API_001_PROD, STAGE_API_001_DEV],
}

# What get_apigatewayv2_stages returns for the APIs in GET_APIS: the raw stage
# lists keyed by API id.
STAGES_BY_API_ID = {
    "api-001": GET_STAGES_RESPONSE_API_001["Items"],
    "api-002": [],
}

# The ARN format of the api-001 stages, matching what WAFv2
# ListResourcesForWebACL returns for API_GATEWAY associations.
STAGE_API_001_PROD_ARN = "arn:aws:apigateway:us-east-1::/apis/api-001/stages/prod"
STAGE_API_001_DEV_ARN = "arn:aws:apigateway:us-east-1::/apis/api-001/stages/dev"
