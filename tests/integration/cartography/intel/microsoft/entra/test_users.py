from datetime import datetime
from datetime import timezone
from typing import Iterator
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j
import pytest
from kiota_abstractions.api_error import APIError
from msgraph.generated.models.directory_object import DirectoryObject
from msgraph.generated.models.sign_in_activity import SignInActivity
from msgraph.generated.models.user import User
from msgraph.generated.models.user_collection_response import UserCollectionResponse
from msgraph.generated.users.users_request_builder import UsersRequestBuilder

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


@pytest.fixture(autouse=True)  # type: ignore[misc]
def isolated_graph(neo4j_session: neo4j.Session) -> Iterator[None]:
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()
    try:
        yield
    finally:
        neo4j_session.run("MATCH (n) DETACH DELETE n").consume()


def test_manager_links_across_activity_availability(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    users = [
        User(
            id="activity-report",
            manager=DirectoryObject(id="basic-manager"),
            sign_in_activity=SignInActivity(),
        ),
        User(id="basic-manager"),
        User(id="basic-report", manager=DirectoryObject(id="activity-manager")),
        User(id="activity-manager", sign_in_activity=SignInActivity()),
    ]
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, TEST_UPDATE_TAG)

    # Act
    load_users(
        neo4j_session, list(transform_users(users)), TEST_TENANT_ID, TEST_UPDATE_TAG
    )

    # Assert
    rows = neo4j_session.run(
        "MATCH (u:EntraUser)-[:REPORTS_TO]->(manager:EntraUser) "
        "WHERE u.id IN ['activity-report', 'basic-report'] "
        "RETURN u.id AS report, manager.id AS manager"
    )
    assert {(row["report"], row["manager"]) for row in rows} == {
        ("activity-report", "basic-manager"),
        ("basic-report", "activity-manager"),
    }


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
                            last_sign_in_date_time=timestamp,
                            last_non_interactive_sign_in_date_time=timestamp,
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
    client.users.UsersRequestBuilderGetRequestConfiguration = (
        UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration
    )
    client.users.UsersRequestBuilderGetQueryParameters = (
        UsersRequestBuilder.UsersRequestBuilderGetQueryParameters
    )

    async def get(
        *,
        request_configuration: UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration,
    ) -> UserCollectionResponse:
        if "signInActivity" in request_configuration.query_parameters.select:
            raise APIError("forbidden", response_status_code=403)
        return UserCollectionResponse(
            value=[
                User(id="retained-user", display_name="Updated synthetic name"),
                User(id="new-user"),
            ]
        )

    client.users.get = AsyncMock(side_effect=get)

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
            "u.last_sign_in_date_time AS interactive, "
            "u.last_non_interactive_sign_in_date_time AS non_interactive, "
            "u.sign_in_activity_available AS available ORDER BY id",
            tenant_id=tenant_id,
        )
    )
    assert [row["id"] for row in rows] == ["new-user", "retained-user"]
    assert rows[0]["successful"] is None
    assert all(
        rows[1][key].to_native() == timestamp
        for key in ("successful", "interactive", "non_interactive")
    )
    assert rows[1]["name"] == "Updated synthetic name"
    assert all(row["available"] is False for row in rows)


@pytest.mark.asyncio  # type: ignore[misc]
async def test_later_page_failure_preserves_existing_inventory(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, 1)
    load_users(
        neo4j_session,
        list(transform_users([User(id="existing-user")])),
        TEST_TENANT_ID,
        1,
    )
    client = MagicMock()
    client.users.get = AsyncMock(
        return_value=UserCollectionResponse(
            value=[User(id="partial-user")],
            odata_next_link="https://graph.microsoft.com/v1.0/users?$skiptoken=synthetic",
        )
    )
    client.users.with_url.return_value.get = AsyncMock(
        side_effect=APIError("forbidden", response_status_code=403)
    )

    # Act and assert
    with (
        patch.object(
            cartography.intel.microsoft.entra.users,
            "GraphServiceClient",
            return_value=client,
        ),
        pytest.raises(APIError),
    ):
        await sync_entra_users(
            neo4j_session,
            TEST_TENANT_ID,
            "synthetic-client",
            "synthetic-secret",
            2,
            {"UPDATE_TAG": 2, "TENANT_ID": TEST_TENANT_ID},
        )
    assert check_nodes(neo4j_session, "EntraUser", ["id", "lastupdated"]) == {
        ("existing-user", 1),
    }
    assert check_rels(
        neo4j_session, "AzureTenant", "id", "EntraUser", "id", "RESOURCE"
    ) == {(TEST_TENANT_ID, "existing-user")}


@patch.object(
    cartography.intel.microsoft.entra.users,
    "GraphServiceClient",
)
@pytest.mark.asyncio
async def test_sync_entra_users(
    mock_client,
    neo4j_session,
):
    """
    Ensure that tenant and users actually get loaded
    """
    # Arrange: Load tenant as prerequisite
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, TEST_UPDATE_TAG)
    mock_client.return_value.users.get = AsyncMock(
        return_value=UserCollectionResponse(value=MOCK_ENTRA_USERS)
    )

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
