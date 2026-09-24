from datetime import datetime
from datetime import timezone
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j
import pytest
from kiota_abstractions.api_error import APIError
from msgraph.generated.models.sign_in_activity import SignInActivity
from msgraph.generated.models.user import User
from msgraph.generated.models.user_collection_response import UserCollectionResponse

import cartography.intel.microsoft.entra.users
from cartography.intel.microsoft.entra.users import load_tenant
from cartography.intel.microsoft.entra.users import load_users
from cartography.intel.microsoft.entra.users import sync_entra_users
from cartography.intel.microsoft.entra.users import transform_users
from tests.data.microsoft.entra.users import MOCK_ENTRA_USERS
from tests.data.microsoft.entra.users import TEST_TENANT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 1234567890


def test_sign_in_activity_datetimes(neo4j_session: neo4j.Session) -> None:
    # Arrange
    timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    user = User(
        id="synthetic-activity-user",
        account_enabled=True,
        sign_in_activity=SignInActivity(
            last_successful_sign_in_date_time=timestamp,
            last_sign_in_date_time=timestamp,
            last_non_interactive_sign_in_date_time=timestamp,
        ),
    )
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, TEST_UPDATE_TAG)

    # Act
    load_users(
        neo4j_session, list(transform_users([user])), TEST_TENANT_ID, TEST_UPDATE_TAG
    )

    # Assert: native datetimes support inactivity filtering.
    result = neo4j_session.run(
        "MATCH (u:EntraUser {id: 'synthetic-activity-user'}) "
        "WHERE u.account_enabled = true "
        "AND u.last_successful_sign_in_date_time < datetime('2024-06-01T00:00:00Z') "
        "RETURN u.last_successful_sign_in_date_time AS successful, "
        "u.last_sign_in_date_time AS interactive, "
        "u.last_non_interactive_sign_in_date_time AS non_interactive"
    ).single()
    assert result is not None
    assert all(value.to_native() == timestamp for value in result.values())


def test_unavailable_activity_preserves_old_timestamps(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, TEST_UPDATE_TAG)
    load_users(
        neo4j_session,
        [
            {
                "id": "synthetic-activity-user",
                "sign_in_activity_available": True,
                "last_successful_sign_in_date_time": timestamp,
                "last_sign_in_date_time": timestamp,
                "last_non_interactive_sign_in_date_time": timestamp,
            }
        ],
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
    )
    user = User(id="synthetic-activity-user")

    # Act
    load_users(
        neo4j_session,
        list(transform_users([user])),
        TEST_TENANT_ID,
        TEST_UPDATE_TAG + 1,
    )

    # Assert: old activity is preserved but marked unavailable for this sync.
    result = neo4j_session.run(
        "MATCH (u:EntraUser {id: 'synthetic-activity-user'}) "
        "RETURN u.last_successful_sign_in_date_time AS successful, "
        "u.last_sign_in_date_time AS interactive, "
        "u.last_non_interactive_sign_in_date_time AS non_interactive, "
        "u.sign_in_activity_available AS available"
    ).single()
    assert result is not None
    assert result["available"] is False
    assert all(
        result[key].to_native() == timestamp
        for key in ("successful", "interactive", "non_interactive")
    )


@pytest.mark.asyncio  # type: ignore[misc]
async def test_permission_fallback_preserves_activity_and_cleans_inventory(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    tenant_id = TEST_TENANT_ID
    timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    load_tenant(neo4j_session, {"id": tenant_id}, 1)
    load_users(
        neo4j_session,
        list(
            transform_users(
                [
                    User(
                        id="retained-user",
                        sign_in_activity=SignInActivity(
                            last_successful_sign_in_date_time=timestamp,
                        ),
                    ),
                    User(id="deleted-user"),
                ]
            )
        ),
        tenant_id,
        1,
    )
    client = MagicMock()
    client.users.get = AsyncMock(
        side_effect=[
            APIError("forbidden", response_status_code=403),
            UserCollectionResponse(
                value=[
                    User(id="retained-user", display_name="Updated synthetic name"),
                    User(id="new-user"),
                ]
            ),
        ]
    )

    # Act
    with patch.object(
        cartography.intel.microsoft.entra.users,
        "GraphServiceClient",
        return_value=client,
    ):
        await sync_entra_users(
            neo4j_session,
            tenant_id,
            "synthetic-client",
            "synthetic-secret",
            2,
            {"UPDATE_TAG": 2, "TENANT_ID": tenant_id},
        )

    # Assert
    rows = list(
        neo4j_session.run(
            "MATCH (:AzureTenant {id: $tenant_id})-[:RESOURCE]->(u:EntraUser) "
            "RETURN u.id AS id, u.display_name AS name, "
            "u.last_successful_sign_in_date_time AS successful, "
            "u.sign_in_activity_available AS available ORDER BY id",
            tenant_id=tenant_id,
        )
    )
    assert [row["id"] for row in rows] == ["new-user", "retained-user"]
    assert rows[0]["successful"] is None
    assert rows[1]["successful"].to_native() == timestamp
    assert rows[1]["name"] == "Updated synthetic name"
    assert all(row["available"] is False for row in rows)


async def _mock_get_users(client):
    """Mock async generator for get_users"""
    for user in MOCK_ENTRA_USERS:
        yield user


@patch.object(
    cartography.intel.microsoft.entra.users,
    "get_users",
    side_effect=_mock_get_users,
)
@pytest.mark.asyncio
async def test_sync_entra_users(
    mock_get_users,
    neo4j_session,
):
    """
    Ensure that tenant and users actually get loaded
    """
    # Arrange: Load tenant as prerequisite
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, TEST_UPDATE_TAG)

    # Act
    await sync_entra_users(
        neo4j_session,
        TEST_TENANT_ID,
        "test-client-id",
        "test-client-secret",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert Tenant exists
    expected_nodes = {
        (TEST_TENANT_ID,),
    }
    assert check_nodes(neo4j_session, "AzureTenant", ["id"]) == expected_nodes

    # Assert Users exist with department and manager_id
    expected_nodes = {
        (
            "ae4ac864-4433-4ba6-96a6-20f8cffdadcb",
            "Homer Simpson",
            "hjsimpson@simpson.corp",
            "Operations",
            "11dca63b-cb03-4e53-bb75-fa8060285550",
        ),
        (
            "11dca63b-cb03-4e53-bb75-fa8060285550",
            "Entra Test User 1",
            "entra-test-user-1@mycompany.onmicrosoft.com",
            "Engineering",
            None,
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "EntraUser",
            ["id", "display_name", "user_principal_name", "department", "manager_id"],
        )
        == expected_nodes
    )

    # Assert Users are linked to their managers
    expected_reports_to_rels = {
        (
            "ae4ac864-4433-4ba6-96a6-20f8cffdadcb",
            "11dca63b-cb03-4e53-bb75-fa8060285550",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraUser",
            "id",
            "EntraUser",
            "id",
            "REPORTS_TO",
        )
        == expected_reports_to_rels
    )

    # Assert Users are connected with Tenant
    expected_rels = {
        ("ae4ac864-4433-4ba6-96a6-20f8cffdadcb", TEST_TENANT_ID),
        ("11dca63b-cb03-4e53-bb75-fa8060285550", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraUser",
            "id",
            "AzureTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
