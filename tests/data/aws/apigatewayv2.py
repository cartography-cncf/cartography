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
