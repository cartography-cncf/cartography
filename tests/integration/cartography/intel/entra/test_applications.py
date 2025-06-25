from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

import cartography.intel.entra.applications
from cartography.intel.entra.applications import sync_entra_applications
from tests.data.entra.applications import MOCK_APP_ROLE_ASSIGNMENTS
from tests.data.entra.applications import MOCK_ENTRA_APPLICATIONS
from tests.data.entra.applications import TEST_CLIENT_ID
from tests.data.entra.applications import TEST_CLIENT_SECRET
from tests.data.entra.applications import TEST_TENANT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 1234567890


@patch.object(
    cartography.intel.entra.applications,
    "get_app_role_assignments",
    new_callable=AsyncMock,
    return_value=MOCK_APP_ROLE_ASSIGNMENTS,
)
@patch.object(
    cartography.intel.entra.applications,
    "get_entra_applications",
    new_callable=AsyncMock,
    return_value=MOCK_ENTRA_APPLICATIONS,
)
@pytest.mark.asyncio
async def test_sync_entra_applications(mock_get, mock_get_assignments, neo4j_session):
    """
    Ensure that applications actually get loaded and connected to tenant,
    and both user-app and group-app relationships exist
    """
    # Setup - Clean up any existing applications and create mock users/groups
    neo4j_session.run(
        """
        // Clean up existing applications and relationships
        MATCH (app:EntraApplication) DETACH DELETE app
    """
    )

    neo4j_session.run(
        """
        CREATE (u1:EntraUser {id: 'ae4ac864-4433-4ba6-96a6-20f8cffdadcb', display_name: 'Test User 1'})
        CREATE (u2:EntraUser {id: '11dca63b-cb03-4e53-bb75-fa8060285550', display_name: 'Test User 2'})
        CREATE (g1:EntraGroup {id: '11111111-2222-3333-4444-555555555555', display_name: 'Finance Team'})
        CREATE (g2:EntraGroup {id: '22222222-3333-4444-5555-666666666666', display_name: 'HR Team'})
    """
    )

    # Act
    await sync_entra_applications(
        neo4j_session,
        TEST_TENANT_ID,
        TEST_CLIENT_ID,
        TEST_CLIENT_SECRET,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert Applications exist
    expected_nodes = {
        ("11111111-1111-1111-1111-111111111111", "Finance Tracker"),
        ("22222222-2222-2222-2222-222222222222", "HR Portal"),
    }
    assert (
        check_nodes(neo4j_session, "EntraApplication", ["id", "display_name"])
        == expected_nodes
    )

    # Assert Applications are connected with Tenant
    expected_rels = {
        ("11111111-1111-1111-1111-111111111111", TEST_TENANT_ID),
        ("22222222-2222-2222-2222-222222222222", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraApplication",
            "id",
            "EntraTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert User-Application relationships exist
    expected_user_app_rels = {
        (
            "ae4ac864-4433-4ba6-96a6-20f8cffdadcb",
            "11111111-1111-1111-1111-111111111111",
        ),
        (
            "11dca63b-cb03-4e53-bb75-fa8060285550",
            "22222222-2222-2222-2222-222222222222",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraUser",
            "id",
            "EntraApplication",
            "id",
            "HAS_APP_ROLE",
        )
        == expected_user_app_rels
    )

    # Assert Group-Application relationships exist
    expected_group_app_rels = {
        (
            "11111111-2222-3333-4444-555555555555",
            "11111111-1111-1111-1111-111111111111",
        ),
        (
            "22222222-3333-4444-5555-666666666666",
            "22222222-2222-2222-2222-222222222222",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraGroup",
            "id",
            "EntraApplication",
            "id",
            "HAS_APP_ROLE",
        )
        == expected_group_app_rels
    )
