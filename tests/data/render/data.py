TEST_OWNER_ID = "tea-test001"

# get() unwraps each list endpoint's `{"<resource_key>": {...}, "cursor": ...}` envelope
# via list_paginated(), so these fixtures represent the already-unwrapped resource objects
# that transform() receives - not the raw wire response.

OWNERS_RESPONSE = [
    {
        "id": TEST_OWNER_ID,
        "name": "cartography-test-workspace",
        "email": "test@example.com",
        "type": "team",
    },
]

PROJECTS_RESPONSE = [
    {
        "id": "prj-test001",
        "name": "cartography-test-project",
        "owner": {
            "id": TEST_OWNER_ID,
            "name": "cartography-test-workspace",
            "email": "test@example.com",
            "type": "team",
        },
        "environmentIds": ["evn-test001"],
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-02T00:00:00Z",
    },
]

ENVIRONMENTS_RESPONSE = [
    {
        "id": "evn-test001",
        "name": "production",
        "projectId": "prj-test001",
        "serviceIds": ["srv-test001"],
        "databasesIds": ["dpg-test001"],
        "protectedStatus": "protected",
        "networkIsolationEnabled": False,
        "ipAllowList": [{"cidrBlock": "0.0.0.0/0", "description": "everywhere"}],
    },
]

SERVICES_RESPONSE = [
    {
        "id": "srv-test001",
        "name": "cartography-test-service",
        "ownerId": TEST_OWNER_ID,
        "environmentId": "evn-test001",
        "type": "static_site",
        "slug": "cartography-test-service",
        "repo": "https://github.com/example/cartography-test-service",
        "branch": "main",
        "rootDir": "",
        "dashboardUrl": "https://dashboard.render.com/web/srv-test001",
        "suspended": "not_suspended",
        "autoDeploy": "yes",
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-02T00:00:00Z",
        "ipAllowList": [{"cidrBlock": "203.0.113.0/24", "description": "office"}],
        "registryCredential": {"id": "crd-test001"},
        "serviceDetails": {
            "runtime": "docker",
            "plan": "starter",
            "region": "oregon",
            "url": "https://cartography-test-service.onrender.com",
            "numInstances": 1,
        },
    },
]

# get_latest_deploy() reads response[0]["deploy"] directly (it does not go through
# list_paginated()), so this fixture is already unwrapped to that inner "deploy" object -
# matching what services.get_latest_deploy() returns to its caller.
LATEST_DEPLOY_RESPONSE = {
    "id": "dep-test001",
    "status": "live",
    "trigger": "api",
    "createdAt": "2026-01-03T00:00:00Z",
    "finishedAt": "2026-01-03T00:05:00Z",
    "commit": {"id": "abc123", "message": "Initial commit"},
    "image": {"ref": "docker.io/example/app:latest"},
}
