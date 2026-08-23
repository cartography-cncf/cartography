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
