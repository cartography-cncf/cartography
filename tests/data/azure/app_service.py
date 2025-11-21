MOCK_APP_SERVICES = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/my-test-app-service",
        "name": "my-test-app-service",
        "kind": "app,linux",
        "location": "East US",
        "state": "Running",
        "default_host_name": "my-test-app-service.azurewebsites.net",
        "https_only": True,
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/my-test-func-app",
        "name": "my-test-func-app",
        "kind": "functionapp,linux",
        "location": "East US",
        "state": "Running",
        "default_host_name": "my-test-func-app.azurewebsites.net",
        "https_only": True,
    },
]
