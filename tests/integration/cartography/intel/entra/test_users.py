from unittest.mock import patch

import pytest

import cartography.intel.entra.users
from cartography.intel.entra.users import load_tenant
from cartography.intel.entra.users import sync_entra_users
from tests.data.entra.users import MOCK_ENTRA_USERS
from tests.data.entra.users import TEST_TENANT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 1234567890


async def _mock_get_users(client):
    """Mock async generator for get_users"""
    for user in MOCK_ENTRA_USERS:
        yield user


@patch.object(
    cartography.intel.entra.users,
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
    assert check_nodes(neo4j_session, "EntraTenant", ["id"]) == expected_nodes

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
            "EntraTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
