# tests/data/azure/functions.py

TEST_FUNCTIONAPP_CODE_ID = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/my-test-func-app"
TEST_FUNCTIONAPP_CONTAINER_ID = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/my-container-func-app"
TEST_FUNCTIONAPP_IMAGE_DIGEST = (
    "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
)
TEST_FUNCTIONAPP_IMAGE_URI = (
    f"myregistry.azurecr.io/func-app:prod@{TEST_FUNCTIONAPP_IMAGE_DIGEST}"
)

MOCK_FUNCTION_APPS = [
    {
        "id": TEST_FUNCTIONAPP_CODE_ID,
        "name": "my-test-func-app",
        "kind": "functionapp",
        "location": "East US",
        "state": "Running",
        "default_host_name": "my-test-func-app.azurewebsites.net",
        "https_only": True,
        "tags": {"env": "prod", "service": "function-app"},
    },
    {
        "id": TEST_FUNCTIONAPP_CONTAINER_ID,
        "name": "my-container-func-app",
        "kind": "functionapp,linux,container",
        "location": "East US",
        "state": "Running",
        "default_host_name": "my-container-func-app.azurewebsites.net",
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

MOCK_FUNCTION_APP_CONFIGS = {
    TEST_FUNCTIONAPP_CODE_ID: {"linux_fx_version": "PYTHON|3.11"},
    TEST_FUNCTIONAPP_CONTAINER_ID: {
        "linux_fx_version": f"DOCKER|{TEST_FUNCTIONAPP_IMAGE_URI}",
    },
}
