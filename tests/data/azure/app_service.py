MOCK_APP_SERVICES = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/my-test-app-service",
        "name": "my-test-app-service",
        "kind": "app,linux",
        "location": "East US",
        "properties": {
            "state": "Running",
            "defaultHostName": "my-test-app-service.azurewebsites.net",
            "httpsOnly": True,
        },
        "tags": {"env": "prod", "service": "app-service"},
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/my-test-func-app",
        "name": "my-test-func-app",
        "kind": "functionapp,linux",
        "location": "East US",
        "properties": {
            "state": "Running",
            "defaultHostName": "my-test-func-app.azurewebsites.net",
            "httpsOnly": True,
        },
        "tags": {"env": "dev", "service": "function-app"},
    },
]
