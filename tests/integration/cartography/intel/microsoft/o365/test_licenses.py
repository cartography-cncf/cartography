from unittest.mock import patch

import pytest

import cartography.intel.microsoft.entra.users
from cartography.intel.microsoft.entra.users import load_tenant
from cartography.intel.microsoft.entra.users import sync_entra_users
from cartography.intel.microsoft.o365.license_details import (
    load_user_license_assignments,
    transform_user_license_assignments,
)
from cartography.intel.microsoft.o365.licenses import (
    load_licenses,
    load_service_plans,
    transform_licenses,
)
from tests.data.microsoft.entra.users import MOCK_ENTRA_USERS
from tests.data.microsoft.entra.users import TEST_TENANT_ID
from tests.data.microsoft.o365.licenses import MOCK_SUBSCRIBED_SKUS
from tests.data.microsoft.o365.licenses import MOCK_USER_LICENSE_DETAILS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 1234567890


async def _mock_get_users(client):
    """Mock async generator for get_users"""
    for user in MOCK_ENTRA_USERS:
        yield user


def _setup_prerequisites(neo4j_session):
    """Load the EntraTenant node as a prerequisite."""
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, TEST_UPDATE_TAG)


def test_transform_licenses():
    """
    Ensure transform_licenses correctly flattens subscribedSkus and deduplicates
    service plans across multiple licenses.
    """
    licenses, service_plans = transform_licenses(MOCK_SUBSCRIBED_SKUS)

    # Two subscribedSkus → two license dicts
    assert len(licenses) == 2
    assert {lic["sku_part_number"] for lic in licenses} == {
        "ENTERPRISEPREMIUM", "EMS",
    }

    # EXCHANGE_S_ENTERPRISE appears in both SKUs but should be deduplicated
    # into one service plan with two license_sku_ids
    assert len(service_plans) == 4  # EXCHANGE, SHAREPOINT, TEAMS, INTUNE
    exchange_plan = next(
        sp for sp in service_plans
        if sp["service_plan_name"] == "EXCHANGE_S_ENTERPRISE"
    )
    assert len(exchange_plan["license_sku_ids"]) == 2


def test_transform_user_license_assignments():
    """
    Ensure transform_user_license_assignments creates flat assignment records.
    """
    assignments = transform_user_license_assignments(MOCK_USER_LICENSE_DETAILS)

    # Homer has 2 licenses, User 1 has 1 → 3 total assignments
    assert len(assignments) == 3
    homer_assignments = [a for a in assignments if a["user_id"] == "ae4ac864-4433-4ba6-96a6-20f8cffdadcb"]
    assert len(homer_assignments) == 2


@patch.object(
    cartography.intel.microsoft.entra.users,
    "get_users",
    side_effect=_mock_get_users,
)
@pytest.mark.asyncio
async def test_sync_o365_licenses(mock_get_users, neo4j_session):
    """
    End-to-end test: load tenant + users, then sync O365 licenses and
    verify all nodes and relationships are created.
    """
    # Arrange: Load tenant and users as prerequisites
    _setup_prerequisites(neo4j_session)
    await sync_entra_users(
        neo4j_session,
        TEST_TENANT_ID,
        "test-client-id",
        "test-client-secret",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
    }

    # Act: Transform and load licenses + service plans
    licenses, service_plans = transform_licenses(MOCK_SUBSCRIBED_SKUS)
    load_licenses(neo4j_session, licenses, TEST_TENANT_ID, TEST_UPDATE_TAG)
    load_service_plans(neo4j_session, service_plans, TEST_TENANT_ID, TEST_UPDATE_TAG)

    # Act: Transform and load user-license assignments
    assignments = transform_user_license_assignments(MOCK_USER_LICENSE_DETAILS)
    load_user_license_assignments(
        neo4j_session, assignments, TEST_TENANT_ID, TEST_UPDATE_TAG,
    )

    # Assert: M365License nodes exist with correct properties
    expected_licenses = {
        ("tenant-sku-e5", "ENTERPRISEPREMIUM", "Enabled", 2, 25),
        ("tenant-sku-ems", "EMS", "Enabled", 1, 10),
    }
    assert (
        check_nodes(
            neo4j_session,
            "M365License",
            ["id", "sku_part_number", "capability_status", "consumed_units", "prepaid_enabled"],
        )
        == expected_licenses
    )

    # Assert: M365ServicePlan nodes exist (deduplicated)
    expected_service_plans = {
        (str(MOCK_SUBSCRIBED_SKUS[0].service_plans[0].service_plan_id), "EXCHANGE_S_ENTERPRISE"),
        (str(MOCK_SUBSCRIBED_SKUS[0].service_plans[1].service_plan_id), "SHAREPOINTENTERPRISE"),
        (str(MOCK_SUBSCRIBED_SKUS[0].service_plans[2].service_plan_id), "TEAMS1"),
        (str(MOCK_SUBSCRIBED_SKUS[1].service_plans[0].service_plan_id), "INTUNE_A"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "M365ServicePlan",
            ["id", "service_plan_name"],
        )
        == expected_service_plans
    )

    # Assert: M365License -> EntraTenant RESOURCE relationship
    expected_license_tenant_rels = {
        ("tenant-sku-e5", TEST_TENANT_ID),
        ("tenant-sku-ems", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "M365License",
            "id",
            "EntraTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_license_tenant_rels
    )

    # Assert: M365License -> M365ServicePlan HAS_SERVICE_PLAN relationship
    # E5 license has 3 service plans, EMS has 2 (Exchange is shared)
    expected_has_sp_rels = {
        ("tenant-sku-e5", str(MOCK_SUBSCRIBED_SKUS[0].service_plans[0].service_plan_id)),
        ("tenant-sku-e5", str(MOCK_SUBSCRIBED_SKUS[0].service_plans[1].service_plan_id)),
        ("tenant-sku-e5", str(MOCK_SUBSCRIBED_SKUS[0].service_plans[2].service_plan_id)),
        ("tenant-sku-ems", str(MOCK_SUBSCRIBED_SKUS[1].service_plans[0].service_plan_id)),
        ("tenant-sku-ems", str(MOCK_SUBSCRIBED_SKUS[0].service_plans[0].service_plan_id)),
    }
    assert (
        check_rels(
            neo4j_session,
            "M365License",
            "id",
            "M365ServicePlan",
            "id",
            "HAS_SERVICE_PLAN",
        )
        == expected_has_sp_rels
    )

    # Assert: EntraUser -> M365License ASSIGNED_LICENSE relationship
    expected_user_license_rels = {
        # Homer -> E5
        ("ae4ac864-4433-4ba6-96a6-20f8cffdadcb", str(MOCK_SUBSCRIBED_SKUS[0].sku_id)),
        # Homer -> EMS
        ("ae4ac864-4433-4ba6-96a6-20f8cffdadcb", str(MOCK_SUBSCRIBED_SKUS[1].sku_id)),
        # User 1 -> E5
        ("11dca63b-cb03-4e53-bb75-fa8060285550", str(MOCK_SUBSCRIBED_SKUS[0].sku_id)),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraUser",
            "id",
            "M365License",
            "sku_id",
            "ASSIGNED_LICENSE",
        )
        == expected_user_license_rels
    )
