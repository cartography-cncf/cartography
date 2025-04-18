from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

import cartography.intel.entra.ou
from cartography.intel.entra.ou import sync_entra_ous
from tests.data.entra.ou import MOCK_ENTRA_OUS
from tests.data.entra.ou import TEST_TENANT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 1234567890


@patch.object(
    cartography.intel.entra.ou,
    'get_entra_ous',
    new_callable=AsyncMock,
    return_value=MOCK_ENTRA_OUS,
)
@pytest.mark.asyncio
async def test_sync_entra_ous(mock_get_ous, neo4j_session):
    """
    Ensure that OUs are loaded and linked to the tenant
    """
    # Arrange
    mock_tenant_id = TEST_TENANT_ID

    # Act
    await sync_entra_ous(
        neo4j_session,
        mock_tenant_id,
        'test-client-id',
        'test-client-secret',
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'TENANT_ID': mock_tenant_id},
    )

    # Assert OUs exist with core fields
    expected_nodes = {
        ('a8f9e4b2-1234-5678-9abc-def012345678', 'Finance Department', 'Public'),
        ('b6c5d3e4-5678-90ab-cdef-1234567890ab', 'IT Operations', 'Private'),
    }
    assert check_nodes(
        neo4j_session,
        'EntraOU',
        ['id', 'display_name', 'visibility'],
    ) == expected_nodes

    # Assert OU-Tenant relationships exist
    expected_rels = {
        ('a8f9e4b2-1234-5678-9abc-def012345678', mock_tenant_id),
        ('b6c5d3e4-5678-90ab-cdef-1234567890ab', mock_tenant_id),
    }
    assert check_rels(
        neo4j_session,
        'EntraOU', 'id',
        'EntraTenant', 'id',
        'BELONGS_TO_TENANT',
        rel_direction_right=False,
    ) == expected_rels

    # Assert full OU properties
    query = """
    MATCH (ou:EntraOU {id: 'a8f9e4b2-1234-5678-9abc-def012345678'})
    RETURN ou.description, ou.membership_type, ou.is_member_management_restricted
    """
    result = neo4j_session.run(query)
    expected_properties = [
        ('Handles financial operations and budgeting', 'Dynamic', False),
    ]
    assert [tuple(record.values()) for record in result] == expected_properties

    # Assert soft-deleted OU is present
    query = """
    MATCH (ou:EntraOU {id: 'b6c5d3e4-5678-90ab-cdef-1234567890ab'})
    RETURN ou.deleted_date_time IS NOT NULL
    """
    result = neo4j_session.run(query)
    assert [record[0] for record in result] == [True]
