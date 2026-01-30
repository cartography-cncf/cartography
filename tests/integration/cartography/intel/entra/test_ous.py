from datetime import timezone
from unittest.mock import patch

import pytest
from neo4j.time import DateTime

import cartography.intel.entra.ou
from cartography.intel.entra.ou import sync_entra_ous
from cartography.intel.entra.users import load_tenant
from tests.data.entra.ou import MOCK_ENTRA_OUS
from tests.data.entra.ou import TEST_CLIENT_ID
from tests.data.entra.ou import TEST_CLIENT_SECRET
from tests.data.entra.ou import TEST_TENANT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 1234567890


async def _mock_get_entra_ous(client):
    """Mock async generator for get_entra_ous"""
    for ou in MOCK_ENTRA_OUS:
        yield ou


@patch.object(
    cartography.intel.entra.ou,
    "get_entra_ous",
    side_effect=_mock_get_entra_ous,
)
@pytest.mark.asyncio
async def test_sync_entra_ous(mock_get_ous, neo4j_session):
    """
    Ensure that OUs are loaded and linked to the tenant
    """
    # Arrange
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, TEST_UPDATE_TAG)

    # Act
    await sync_entra_ous(
        neo4j_session,
        TEST_TENANT_ID,
        TEST_CLIENT_ID,
        TEST_CLIENT_SECRET,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert OUs exist with core fields
    expected_nodes = {
        ("a8f9e4b2-1234-5678-9abc-def012345678", "Finance Department", "Public"),
        ("b6c5d3e4-5678-90ab-cdef-1234567890ab", "IT Operations", "Private"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "EntraOU",
            ["id", "display_name", "visibility"],
        )
        == expected_nodes
    )

    # Assert OU-Tenant relationships exist
    expected_rels = {
        ("a8f9e4b2-1234-5678-9abc-def012345678", TEST_TENANT_ID),
        ("b6c5d3e4-5678-90ab-cdef-1234567890ab", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraOU",
            "id",
            "EntraTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert full OU properties
    expected_properties = {
        (
            "a8f9e4b2-1234-5678-9abc-def012345678",
            "Handles financial operations and budgeting",
            "Dynamic",
            False,
        ),
        (
            "b6c5d3e4-5678-90ab-cdef-1234567890ab",
            "Manages IT infrastructure and support",
            "Assigned",
            True,
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "EntraOU",
            ["id", "description", "membership_type", "is_member_management_restricted"],
        )
        == expected_properties
    )

    # Assert soft-deleted OU is present
    expected_properties = {
        ("a8f9e4b2-1234-5678-9abc-def012345678", None),
        (
            "b6c5d3e4-5678-90ab-cdef-1234567890ab",
            DateTime(2025, 3, 1, 12, 0, 0, 0, tzinfo=timezone.utc),
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "EntraOU",
            ["id", "deleted_date_time"],
        )
        == expected_properties
    )
