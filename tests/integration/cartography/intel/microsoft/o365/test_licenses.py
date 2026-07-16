from unittest.mock import patch

import pytest

import cartography.intel.microsoft.entra.users
from cartography.intel.microsoft.entra.users import load_tenant
from cartography.intel.microsoft.entra.users import sync_entra_users
from cartography.intel.microsoft.o365.license_details import (
    load_user_license_assignments,
)
from cartography.intel.microsoft.o365.license_details import (
    transform_user_license_assignments,
)
from cartography.intel.microsoft.o365.licenses import cleanup_licenses
from cartography.intel.microsoft.o365.licenses import cleanup_service_plans
from cartography.intel.microsoft.o365.licenses import load_licenses
from cartography.intel.microsoft.o365.licenses import load_service_plans
from cartography.intel.microsoft.o365.licenses import transform_licenses
from tests.data.microsoft.entra.users import MOCK_ENTRA_USERS
from tests.data.microsoft.entra.users import TEST_TENANT_ID
from tests.data.microsoft.o365.licenses import MOCK_SUBSCRIBED_SKUS
from tests.data.microsoft.o365.licenses import MOCK_USER_ASSIGNED_LICENSES
from tests.data.microsoft.o365.licenses import SP_EXCHANGE
from tests.data.microsoft.o365.licenses import SP_INTUNE
from tests.data.microsoft.o365.licenses import SP_SHAREPOINT
from tests.data.microsoft.o365.licenses import SP_TEAMS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 1234567890
TEST_UPDATE_TAG_2 = 1234567891

# A different tenant for multi-tenant isolation testing
TEST_TENANT_ID_B = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


async def _mock_get_users(client):
    """Mock async generator for get_users"""
    for user in MOCK_ENTRA_USERS:
        yield user


def _setup_prerequisites(neo4j_session):
    """Load the AzureTenant node as a prerequisite."""
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, TEST_UPDATE_TAG)


def _do_full_sync(neo4j_session, tenant_id, update_tag, common_job_parameters):
    """
    Run complete sync cycle: transform, load, cleanup.
    """
    # Transform and load licenses + service plans
    licenses, service_plans = transform_licenses(MOCK_SUBSCRIBED_SKUS, tenant_id)
    load_licenses(neo4j_session, licenses, tenant_id, update_tag)
    load_service_plans(neo4j_session, service_plans, tenant_id, update_tag)

    # Transform and load user-license assignments
    assignments = transform_user_license_assignments(MOCK_USER_ASSIGNED_LICENSES)
    load_user_license_assignments(neo4j_session, assignments, tenant_id, update_tag)

    # Run cleanup jobs
    cleanup_licenses(neo4j_session, common_job_parameters)
    cleanup_service_plans(neo4j_session, common_job_parameters)


def test_transform_licenses():
    """
    Ensure transform_licenses flattens SKUs and scopes SP IDs.
    """
    licenses, service_plans = transform_licenses(MOCK_SUBSCRIBED_SKUS, TEST_TENANT_ID)

    # Two subscribedSkus → two license dicts
    assert len(licenses) == 2
    assert {lic["sku_part_number"] for lic in licenses} == {
        "ENTERPRISEPREMIUM",
        "EMS",
    }

    # EXCHANGE_S_ENTERPRISE appears in both SKUs but should be deduplicated
    # into one service plan with two license_ids
    assert len(service_plans) == 4  # EXCHANGE, SHAREPOINT, TEAMS, INTUNE
    exchange_plan = next(
        sp for sp in service_plans if sp["service_plan_name"] == "EXCHANGE_S_ENTERPRISE"
    )
    assert len(exchange_plan["license_ids"]) == 2

    # Verify that service plan IDs are scoped to tenant
    for sp in service_plans:
        assert sp["id"].startswith(f"{TEST_TENANT_ID}-")
        assert sp["service_plan_id"]  # Original UUID preserved


def test_transform_user_license_assignments():
    """
    Ensure assignments are flattened correctly.
    """
    assignments = transform_user_license_assignments(MOCK_USER_ASSIGNED_LICENSES)

    # Homer has 2 licenses, User 1 has 1 → 3 total assignments
    assert len(assignments) == 3
    homer_assignments = [
        a for a in assignments if a["user_id"] == "ae4ac864-4433-4ba6-96a6-20f8cffdadcb"
    ]
    assert len(homer_assignments) == 2


@patch.object(
    cartography.intel.microsoft.entra.users,
    "get_users",
    side_effect=_mock_get_users,
)
@pytest.mark.asyncio
async def test_sync_o365_licenses(mock_get_users, neo4j_session):
    """
    End-to-end sync test verifying nodes and relationships.
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

    # Act: Run full sync cycle
    _do_full_sync(neo4j_session, TEST_TENANT_ID, TEST_UPDATE_TAG, common_job_parameters)

    # Assert: M365License nodes exist with correct properties
    expected_licenses = {
        ("tenant-sku-e5", "ENTERPRISEPREMIUM", "Enabled", 2, 25),
        ("tenant-sku-ems", "EMS", "Enabled", 1, 10),
    }
    assert (
        check_nodes(
            neo4j_session,
            "M365License",
            [
                "id",
                "sku_part_number",
                "capability_status",
                "consumed_units",
                "prepaid_enabled",
            ],
        )
        == expected_licenses
    )

    # Assert: M365ServicePlan nodes exist (deduplicated) with tenant-scoped IDs
    expected_service_plans = {
        (f"{TEST_TENANT_ID}-{SP_EXCHANGE}", "EXCHANGE_S_ENTERPRISE"),
        (f"{TEST_TENANT_ID}-{SP_SHAREPOINT}", "SHAREPOINTENTERPRISE"),
        (f"{TEST_TENANT_ID}-{SP_TEAMS}", "TEAMS1"),
        (f"{TEST_TENANT_ID}-{SP_INTUNE}", "INTUNE_A"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "M365ServicePlan",
            ["id", "service_plan_name"],
        )
        == expected_service_plans
    )

    # Assert: M365License -> AzureTenant RESOURCE relationship
    expected_license_tenant_rels = {
        ("tenant-sku-e5", TEST_TENANT_ID),
        ("tenant-sku-ems", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "M365License",
            "id",
            "AzureTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_license_tenant_rels
    )

    # Assert: M365License -> M365ServicePlan HAS_SERVICE_PLAN relationship
    # E5 license has 3 service plans, EMS has 2 (Exchange is shared)
    expected_has_sp_rels = {
        ("tenant-sku-e5", f"{TEST_TENANT_ID}-{SP_EXCHANGE}"),
        ("tenant-sku-e5", f"{TEST_TENANT_ID}-{SP_SHAREPOINT}"),
        ("tenant-sku-e5", f"{TEST_TENANT_ID}-{SP_TEAMS}"),
        ("tenant-sku-ems", f"{TEST_TENANT_ID}-{SP_INTUNE}"),
        ("tenant-sku-ems", f"{TEST_TENANT_ID}-{SP_EXCHANGE}"),
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


@patch.object(
    cartography.intel.microsoft.entra.users,
    "get_users",
    side_effect=_mock_get_users,
)
@pytest.mark.asyncio
async def test_multi_tenant_cleanup_isolation(mock_get_users, neo4j_session):
    """
    Verify cleanup of Tenant A does not delete Tenant B nodes.
    """
    # --- Arrange: Sync data for Tenant A ---
    _setup_prerequisites(neo4j_session)
    await sync_entra_users(
        neo4j_session,
        TEST_TENANT_ID,
        "test-client-id",
        "test-client-secret",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    common_job_params_a = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
    }
    _do_full_sync(
        neo4j_session,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_params_a,
    )

    # --- Arrange: Sync data for Tenant B ---
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID_B}, TEST_UPDATE_TAG)

    licenses_b, service_plans_b = transform_licenses(
        MOCK_SUBSCRIBED_SKUS,
        TEST_TENANT_ID_B,
    )
    load_licenses(neo4j_session, licenses_b, TEST_TENANT_ID_B, TEST_UPDATE_TAG)
    load_service_plans(
        neo4j_session,
        service_plans_b,
        TEST_TENANT_ID_B,
        TEST_UPDATE_TAG,
    )

    # Verify both tenants' service plans exist before cleanup
    all_sp_ids = check_nodes(neo4j_session, "M365ServicePlan", ["id"])
    tenant_a_plans = {sp for sp in all_sp_ids if TEST_TENANT_ID in next(iter(sp))}
    tenant_b_plans = {sp for sp in all_sp_ids if TEST_TENANT_ID_B in next(iter(sp))}
    assert len(tenant_a_plans) == 4
    assert len(tenant_b_plans) == 4

    # --- Act: Run cleanup for Tenant A with a NEW update tag ---
    # This simulates a new sync cycle for Tenant A that produced no data,
    # so all of Tenant A's old nodes should be cleaned up.
    common_job_params_a_new = {
        "UPDATE_TAG": TEST_UPDATE_TAG_2,
        "TENANT_ID": TEST_TENANT_ID,
    }
    cleanup_licenses(neo4j_session, common_job_params_a_new)
    cleanup_service_plans(neo4j_session, common_job_params_a_new)

    # --- Assert: Tenant A's nodes are gone, Tenant B's survive ---
    remaining_sp_ids = check_nodes(neo4j_session, "M365ServicePlan", ["id"])
    remaining_a = {sp for sp in remaining_sp_ids if TEST_TENANT_ID in next(iter(sp))}
    remaining_b = {sp for sp in remaining_sp_ids if TEST_TENANT_ID_B in next(iter(sp))}

    # Tenant A's service plans should have been cleaned up
    assert (
        len(remaining_a) == 0
    ), f"Expected Tenant A service plans to be cleaned up, but found: {remaining_a}"
    # Tenant B's service plans should be untouched
    assert (
        len(remaining_b) == 4
    ), f"Tenant B service plans should survive cleanup of Tenant A, found: {remaining_b}"


@patch.object(
    cartography.intel.microsoft.entra.users,
    "get_users",
    side_effect=_mock_get_users,
)
@pytest.mark.asyncio
async def test_stale_data_preserved_on_failure(mock_get_users, neo4j_session):
    """
    Verify old data is preserved when sync fails (cleanup skipped).
    """
    # --- Arrange: Successful first sync cycle ---
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
    _do_full_sync(
        neo4j_session,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Verify initial data is loaded
    licenses_before = check_nodes(neo4j_session, "M365License", ["id"])
    assert len(licenses_before) == 2

    # --- Act: Simulate failed second sync cycle ---
    # Don't load any new data, but DON'T run cleanup either (simulating
    # the orchestrator aborting before cleanup on API error).
    # This is the correct behavior: no cleanup = stale data preserved.

    # --- Assert: Old data still intact ---
    licenses_after = check_nodes(neo4j_session, "M365License", ["id"])
    assert (
        licenses_after == licenses_before
    ), "License nodes should be preserved when sync fails before cleanup"

    service_plans_after = check_nodes(neo4j_session, "M365ServicePlan", ["id"])
    # Filter to only this tenant's service plans (other tests may have
    # loaded additional tenants into the shared Neo4j session).
    tenant_plans_after = {
        sp for sp in service_plans_after if TEST_TENANT_ID in next(iter(sp))
    }
    assert (
        len(tenant_plans_after) == 4
    ), "Service plan nodes should be preserved when sync fails before cleanup"
