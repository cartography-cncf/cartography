# Testing reference

**Key principle: test outcomes, not implementation details.**

Verify data is written to the graph as expected. Mock external dependencies (APIs, credentials, network) but never internal Cartography sync / load / cleanup functions.

## Contents

- Test data
- Integration test
- What to test
- When to mock
- Integration test boundary

## Test data

Mock API payloads live in `tests/data/your_service/`:

```python
# tests/data/your_service/users.py
MOCK_USERS_RESPONSE = {
    "users": [
        {
            "id": "user-123",
            "email": "alice@example.com",
            "display_name": "Alice Smith",
            "created_at": "2023-01-15T10:30:00Z",
            "last_login": "2023-12-01T14:22:00Z",
            "is_admin": False,
        },
        {
            "id": "user-456",
            "email": "bob@example.com",
            "display_name": "Bob Jones",
            "created_at": "2023-02-20T16:45:00Z",
            "last_login": None,
            "is_admin": True,
        },
    ]
}
```

## Integration test

```python
# tests/integration/cartography/intel/your_service/test_users.py
from unittest.mock import patch

import cartography.intel.your_service.users
from tests.data.your_service.users import MOCK_USERS_RESPONSE
from tests.integration.util import check_nodes, check_rels


TEST_UPDATE_TAG = 123456789
TEST_TENANT_ID = "tenant-123"


@patch.object(
    cartography.intel.your_service.users,
    "get",
    return_value=MOCK_USERS_RESPONSE,
)
def test_sync_users(mock_api, neo4j_session):
    cartography.intel.your_service.users.sync(
        neo4j_session,
        "fake-api-key",
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    expected_nodes = {
        ("user-123", "alice@example.com"),
        ("user-456", "bob@example.com"),
    }
    assert check_nodes(neo4j_session, "YourServiceUser", ["id", "email"]) == expected_nodes

    assert check_nodes(neo4j_session, "YourServiceTenant", ["id"]) == {(TEST_TENANT_ID,)}

    expected_rels = {
        ("user-123", TEST_TENANT_ID),
        ("user-456", TEST_TENANT_ID),
    }
    assert check_rels(
        neo4j_session,
        "YourServiceUser", "id",
        "YourServiceTenant", "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == expected_rels
```

## What to test

**DO** test outcomes:
- Nodes created with correct properties.
- Relationships created between expected nodes.

**DO NOT** test implementation details:
- Mock parameter values (brittle).
- Internal call order.
- Mock call counts unless absolutely necessary.

## When to mock

**DO** mock external boundaries:
- Third-party APIs (AWS, Azure, SaaS providers).
- Credentials / authentication.
- Network calls.

**DO NOT** mock:
- Internal Cartography functions.
- Data transformation logic.
- The function under test.

## Integration test boundary

- Tests may seed prerequisite graph state with Cypher, but should exercise real Cartography `sync()` / `sync_*()` flows end-to-end whenever practical.
- Mock only external boundaries (API clients, service discovery, credentials, network responses); do not mock Cartography internal sync, load, or cleanup functions in integration tests.
