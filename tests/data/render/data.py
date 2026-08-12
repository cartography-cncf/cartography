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
        "type": "web_service",
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
        "serviceDetails": {
            "runtime": "docker",
            "plan": "starter",
            "region": "oregon",
            "url": "https://cartography-test-service.onrender.com",
            "numInstances": 1,
            "disk": {
                "id": "dsk-test001",
                "name": "data",
                "sizeGB": 1,
                "mountPath": "/data",
            },
        },
    },
]

DISKS_RESPONSE = [
    {
        "id": "dsk-test001",
        "name": "data",
        "serviceId": "srv-test001",
        "sizeGB": 1,
        "mountPath": "/data",
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-02T00:00:00Z",
    },
]

CUSTOM_DOMAINS_RESPONSE = [
    {
        "id": "cdm-test001",
        "name": "www.example.com",
        "domainType": "subdomain",
        "publicSuffix": "com",
        "redirectForName": None,
        "verificationStatus": "verified",
        "createdAt": "2026-01-01T00:00:00Z",
    },
]

# `content` mirrors what the live API actually returns alongside `name`, so tests can
# assert it is discarded rather than merely absent from the fixture.
SECRET_FILES_RESPONSE = [
    {
        "name": ".env",
        "content": "SUPER_SECRET_VALUE=do-not-ingest-me",
    },
]

POSTGRES_RESPONSE = [
    {
        "id": "dpg-test001",
        "name": "cartography-test-db",
        "owner": {
            "id": TEST_OWNER_ID,
            "name": "cartography-test-workspace",
            "email": "test@example.com",
            "type": "team",
        },
        "environmentId": "evn-test001",
        "databaseName": "cartography_test",
        "databaseUser": "cartography_test_user",
        "plan": "starter",
        "region": "oregon",
        "version": "16",
        "status": "available",
        "suspended": "not_suspended",
        "highAvailabilityEnabled": False,
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-02T00:00:00Z",
        "ipAllowList": [{"cidrBlock": "203.0.113.0/24", "description": "office"}],
    },
]

KEY_VALUE_RESPONSE = [
    {
        "id": "red-test001",
        "name": "cartography-test-kv",
        "owner": {
            "id": TEST_OWNER_ID,
            "name": "cartography-test-workspace",
            "email": "test@example.com",
            "type": "team",
        },
        "environmentId": "evn-test001",
        "status": "available",
        "region": "oregon",
        "plan": "free",
        "version": "8",
        "dashboardUrl": "https://dashboard.render.com/redis/red-test001",
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-02T00:00:00Z",
        "ipAllowList": [{"cidrBlock": "0.0.0.0/0", "description": "everywhere"}],
    },
]

DEDICATED_IPS_RESPONSE = [
    {
        "id": "dip-test001",
        "name": "cartography-test-dedicated-ip",
        "description": "",
        "ownerId": TEST_OWNER_ID,
        "region": "oregon",
        "environmentIds": ["evn-test001"],
        "ips": ["203.0.113.42"],
        "status": "RUNNING",
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-02T00:00:00Z",
    },
]

# Env var/secret file values are never returned by GET /env-groups (metadata only), so
# there is nothing to discard here the way secretfiles.py discards `content`.
ENV_GROUPS_RESPONSE = [
    {
        "id": "evg-test001",
        "name": "cartography-test-env-group",
        "ownerId": TEST_OWNER_ID,
        "environmentId": "evn-test001",
        "serviceLinks": [
            {
                "id": "srv-test001",
                "name": "cartography-test-service",
                "type": "web_service",
            }
        ],
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-02T00:00:00Z",
    },
]
