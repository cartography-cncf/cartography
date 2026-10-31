# Testing reference

Follow [tests/AGENTS.md](../../../../tests/AGENTS.md) for test scope, assertions,
mocking, and fixtures. This example exercises real ingestion with provider input
mocked at `get()` and checks the resulting relationships.

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
from tests.integration.util import check_rels


TEST_UPDATE_TAG = 123456789
TEST_TENANT_ID = "tenant-123"


@patch.object(
    cartography.intel.your_service.users,
    "get",
    return_value=MOCK_USERS_RESPONSE,
)
def test_sync_users(mock_api, neo4j_session):
    # Arrange: provider input is supplied by the patch above.
    # The tenant is a prerequisite normally loaded by the module entry point.
    neo4j_session.run(
        "MERGE (:YourServiceTenant {id: $id})", id=TEST_TENANT_ID,
    )

    # Act
    cartography.intel.your_service.users.sync(
        neo4j_session,
        "fake-api-key",
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert
    expected_rels = {
        ("user-123", TEST_TENANT_ID),
        ("user-456", TEST_TENANT_ID),
    }
    assert check_rels(
        neo4j_session,
        "YourServiceUser", "id",
        "YourServiceTenant", "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == expected_rels
```
