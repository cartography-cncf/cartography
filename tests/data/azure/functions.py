# tests/data/azure/functions.py

MOCK_FUNCTION_APPS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/my-test-func-app",
        "name": "my-test-func-app",
        "kind": "functionapp",
        "location": "East US",
        "state": "Running",
        "default_host_name": "my-test-func-app.azurewebsites.net",
        "https_only": True,
        "tags": {"env": "prod", "service": "function-app"},
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/my-regular-web-app",
        "name": "my-regular-web-app",
        "kind": "app",
        "location": "East US",
        "state": "Running",
        "default_host_name": "my-regular-web-app.azurewebsites.net",
        "https_only": True,
        "tags": {"env": "prod", "service": "web-app"},
    },
]
