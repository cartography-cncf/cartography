from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from kiota_abstractions.api_error import APIError

import cartography.intel.microsoft.entra.users
import cartography.intel.microsoft.o365.license_details
import cartography.intel.microsoft.o365.licenses
from cartography.intel.microsoft.entra.users import load_tenant
from cartography.intel.microsoft.entra.users import sync_entra_users
from cartography.intel.microsoft.o365.license_details import (
    cleanup_user_license_assignments,
)
from cartography.intel.microsoft.o365.license_details import sync_user_license_details
from cartography.intel.microsoft.o365.licenses import cleanup_licenses
from cartography.intel.microsoft.o365.licenses import cleanup_service_plans
from cartography.intel.microsoft.o365.licenses import sync_licenses
from cartography.intel.microsoft.o365.licenses import transform_licenses
from tests.data.microsoft.entra.users import TEST_TENANT_ID
from tests.data.microsoft.o365.licenses import make_subscribed_skus
from tests.data.microsoft.o365.licenses import MOCK_SUBSCRIBED_SKUS
from tests.data.microsoft.o365.licenses import MOCK_USER_ASSIGNED_LICENSES
from tests.data.microsoft.o365.licenses import SKU_ID_E5
from tests.data.microsoft.o365.licenses import SKU_ID_EMS
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
    """Mock async generator for get_users."""
    from tests.data.microsoft.entra.users import MOCK_ENTRA_USERS

    for user in MOCK_ENTRA_USERS:
        yield user


def _setup_tenant_and_users(neo4j_session, tenant_id=TEST_TENANT_ID):
    """Load AzureTenant + EntraUser nodes as prerequisites."""
    load_tenant(neo4j_session, {"id": tenant_id}, TEST_UPDATE_TAG)


# ── Pure-transform tests (no Neo4j) ──────────────────────────────


def test_transform_licenses():
    """Ensure transform_licenses flattens SKUs and scopes SP IDs."""
    licenses, service_plans = transform_licenses(MOCK_SUBSCRIBED_SKUS, TEST_TENANT_ID)

    assert len(licenses) == 2
    assert {lic["sku_part_number"] for lic in licenses} == {
        "ENTERPRISEPREMIUM",
        "EMS",
    }

    # EXCHANGE appears in both SKUs but is deduplicated
    assert len(service_plans) == 4
    exchange_plan = next(
        sp for sp in service_plans if sp["service_plan_name"] == "EXCHANGE_S_ENTERPRISE"
    )
    assert len(exchange_plan["license_ids"]) == 2

    # Service plan IDs are scoped to tenant
    for sp in service_plans:
        assert sp["id"].startswith(f"{TEST_TENANT_ID}-")
        assert sp["service_plan_id"]


def test_transform_licenses_tenant_scoped_sku_ids():
    """Ensure factory-generated SKU IDs follow {tenantId}_{skuId} format."""
    skus = make_subscribed_skus("tenant-aaa")
    licenses, _ = transform_licenses(skus, "tenant-aaa")

    for lic in licenses:
        assert lic["id"].startswith("tenant-aaa_")


# ── Sync-level tests (drive actual sync_licenses / sync_user_license_details) ─


@patch.object(
    cartography.intel.microsoft.entra.users,
    "get_users",
    side_effect=_mock_get_users,
)
@patch.object(
    cartography.intel.microsoft.o365.licenses,
    "get_subscribed_skus",
    new_callable=AsyncMock,
    return_value=MOCK_SUBSCRIBED_SKUS,
)
@patch.object(
    cartography.intel.microsoft.o365.license_details,
    "get_users_with_assigned_licenses",
    new_callable=AsyncMock,
    return_value=(MOCK_USER_ASSIGNED_LICENSES, False),
)
@pytest.mark.asyncio
async def test_sync_o365_licenses(
    mock_get_user_licenses,
    mock_get_skus,
    mock_get_users,
    neo4j_session,
):
    """End-to-end sync test driving the real sync_* functions."""
    _setup_tenant_and_users(neo4j_session)
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

    # Drive the actual sync_licenses function (GET→TRANSFORM→LOAD→CLEANUP)
    await sync_licenses(
        neo4j_session, None, TEST_TENANT_ID, TEST_UPDATE_TAG, common_job_parameters,
    )

    # Drive the actual sync_user_license_details function
    has_failures = await sync_user_license_details(
        neo4j_session, None, TEST_TENANT_ID, TEST_UPDATE_TAG,
    )
    assert not has_failures

    # Cleanup should run because has_failures is False
    cleanup_user_license_assignments(neo4j_session, TEST_TENANT_ID, TEST_UPDATE_TAG)

    # Assert: M365License nodes with tenant-scoped IDs
    expected_licenses = {
        (f"{TEST_TENANT_ID}_{SKU_ID_E5}", "ENTERPRISEPREMIUM", "Enabled", 2, 25),
        (f"{TEST_TENANT_ID}_{SKU_ID_EMS}", "EMS", "Enabled", 1, 10),
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

    # Assert: M365ServicePlan nodes (deduplicated) with tenant-scoped IDs
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

    # Assert: M365License -> AzureTenant RESOURCE
    expected_license_tenant_rels = {
        (f"{TEST_TENANT_ID}_{SKU_ID_E5}", TEST_TENANT_ID),
        (f"{TEST_TENANT_ID}_{SKU_ID_EMS}", TEST_TENANT_ID),
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

    # Assert: M365License -> M365ServicePlan HAS_SERVICE_PLAN
    expected_has_sp_rels = {
        (f"{TEST_TENANT_ID}_{SKU_ID_E5}", f"{TEST_TENANT_ID}-{SP_EXCHANGE}"),
        (f"{TEST_TENANT_ID}_{SKU_ID_E5}", f"{TEST_TENANT_ID}-{SP_SHAREPOINT}"),
        (f"{TEST_TENANT_ID}_{SKU_ID_E5}", f"{TEST_TENANT_ID}-{SP_TEAMS}"),
        (f"{TEST_TENANT_ID}_{SKU_ID_EMS}", f"{TEST_TENANT_ID}-{SP_INTUNE}"),
        (f"{TEST_TENANT_ID}_{SKU_ID_EMS}", f"{TEST_TENANT_ID}-{SP_EXCHANGE}"),
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

    # Assert: EntraUser -> M365License ASSIGNED_LICENSE
    expected_user_license_rels = {
        ("ae4ac864-4433-4ba6-96a6-20f8cffdadcb", str(SKU_ID_E5)),
        ("ae4ac864-4433-4ba6-96a6-20f8cffdadcb", str(SKU_ID_EMS)),
        ("11dca63b-cb03-4e53-bb75-fa8060285550", str(SKU_ID_E5)),
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
    cartography.intel.microsoft.o365.licenses,
    "get_subscribed_skus",
    new_callable=AsyncMock,
)
@pytest.mark.asyncio
async def test_sync_licenses_403_skips_gracefully(mock_get_skus, neo4j_session):
    """A 403 from get_subscribed_skus raises APIError; orchestrator catches it."""
    # Snapshot nodes before (shared session may have data from earlier tests)
    nodes_before = check_nodes(neo4j_session, "M365License", ["id"])

    err = APIError("forbidden")
    err.response_status_code = 403
    mock_get_skus.side_effect = err

    _setup_tenant_and_users(neo4j_session)

    # sync_licenses itself does not catch the 403 — the orchestrator does.
    # Verify the error propagates so the orchestrator can handle it.
    with pytest.raises(APIError) as exc_info:
        await sync_licenses(
            neo4j_session,
            None,
            TEST_TENANT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
        )
    assert exc_info.value.response_status_code == 403

    # No new license nodes should have been created
    nodes_after = check_nodes(neo4j_session, "M365License", ["id"])
    assert nodes_after == nodes_before


@patch.object(
    cartography.intel.microsoft.entra.users,
    "get_users",
    side_effect=_mock_get_users,
)
@patch.object(
    cartography.intel.microsoft.o365.licenses,
    "get_subscribed_skus",
    new_callable=AsyncMock,
    return_value=MOCK_SUBSCRIBED_SKUS,
)
@patch.object(
    cartography.intel.microsoft.o365.license_details,
    "get_users_with_assigned_licenses",
    new_callable=AsyncMock,
)
@pytest.mark.asyncio
async def test_sync_user_license_details_pagination_failure_skips_cleanup(
    mock_get_user_licenses,
    mock_get_skus,
    mock_get_users,
    neo4j_session,
):
    """When pagination fails, has_failures=True and cleanup is skipped."""
    _setup_tenant_and_users(neo4j_session)
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

    # -- Cycle 1: successful sync --
    mock_get_user_licenses.return_value = (MOCK_USER_ASSIGNED_LICENSES, False)
    await sync_licenses(
        neo4j_session, None, TEST_TENANT_ID, TEST_UPDATE_TAG, common_job_parameters,
    )
    has_failures = await sync_user_license_details(
        neo4j_session, None, TEST_TENANT_ID, TEST_UPDATE_TAG,
    )
    assert not has_failures
    cleanup_user_license_assignments(neo4j_session, TEST_TENANT_ID, TEST_UPDATE_TAG)

    assignments_before = check_rels(
        neo4j_session, "EntraUser", "id", "M365License", "sku_id", "ASSIGNED_LICENSE",
    )
    assert len(assignments_before) == 3

    # -- Cycle 2: pagination failure → has_failures=True --
    # Return partial data + failure flag
    partial_data = {
        "ae4ac864-4433-4ba6-96a6-20f8cffdadcb": MOCK_USER_ASSIGNED_LICENSES[
            "ae4ac864-4433-4ba6-96a6-20f8cffdadcb"
        ],
    }
    mock_get_user_licenses.return_value = (partial_data, True)

    has_failures = await sync_user_license_details(
        neo4j_session, None, TEST_TENANT_ID, TEST_UPDATE_TAG_2,
    )
    assert has_failures

    # Orchestrator skips cleanup when has_failures is True.
    # Do NOT call cleanup_user_license_assignments here.

    # All 3 original assignments survive (stale data preserved)
    assignments_after = check_rels(
        neo4j_session, "EntraUser", "id", "M365License", "sku_id", "ASSIGNED_LICENSE",
    )
    assert assignments_after == assignments_before


@patch.object(
    cartography.intel.microsoft.entra.users,
    "get_users",
    side_effect=_mock_get_users,
)
@pytest.mark.asyncio
async def test_multi_tenant_cleanup_isolation(mock_get_users, neo4j_session):
    """Cleanup of Tenant A does not delete Tenant B's licenses or service plans."""
    # -- Tenant A setup --
    _setup_tenant_and_users(neo4j_session, TEST_TENANT_ID)
    await sync_entra_users(
        neo4j_session,
        TEST_TENANT_ID,
        "test-client-id",
        "test-client-secret",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    skus_a = make_subscribed_skus(TEST_TENANT_ID)
    common_a = {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID}

    with patch.object(
        cartography.intel.microsoft.o365.licenses,
        "get_subscribed_skus",
        new_callable=AsyncMock,
        return_value=skus_a,
    ):
        await sync_licenses(
            neo4j_session, None, TEST_TENANT_ID, TEST_UPDATE_TAG, common_a,
        )

    # -- Tenant B setup --
    _setup_tenant_and_users(neo4j_session, TEST_TENANT_ID_B)

    skus_b = make_subscribed_skus(TEST_TENANT_ID_B)
    common_b = {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID_B}

    with patch.object(
        cartography.intel.microsoft.o365.licenses,
        "get_subscribed_skus",
        new_callable=AsyncMock,
        return_value=skus_b,
    ):
        await sync_licenses(
            neo4j_session, None, TEST_TENANT_ID_B, TEST_UPDATE_TAG, common_b,
        )

    # Verify both tenants have distinct nodes
    all_license_ids = check_nodes(neo4j_session, "M365License", ["id"])
    a_licenses = {n for n in all_license_ids if TEST_TENANT_ID in next(iter(n))}
    b_licenses = {n for n in all_license_ids if TEST_TENANT_ID_B in next(iter(n))}
    assert len(a_licenses) == 2
    assert len(b_licenses) == 2

    all_sp_ids = check_nodes(neo4j_session, "M365ServicePlan", ["id"])
    a_plans = {n for n in all_sp_ids if TEST_TENANT_ID in next(iter(n))}
    b_plans = {n for n in all_sp_ids if TEST_TENANT_ID_B in next(iter(n))}
    assert len(a_plans) == 4
    assert len(b_plans) == 4

    # -- Cleanup Tenant A with new update tag (empty sync cycle) --
    common_a_new = {"UPDATE_TAG": TEST_UPDATE_TAG_2, "TENANT_ID": TEST_TENANT_ID}
    cleanup_licenses(neo4j_session, common_a_new)
    cleanup_service_plans(neo4j_session, common_a_new)

    # Tenant A's nodes are gone
    remaining_licenses = check_nodes(neo4j_session, "M365License", ["id"])
    remaining_a_lic = {
        n for n in remaining_licenses if TEST_TENANT_ID in next(iter(n))
    }
    assert len(remaining_a_lic) == 0, f"Expected 0, got: {remaining_a_lic}"

    remaining_sps = check_nodes(neo4j_session, "M365ServicePlan", ["id"])
    remaining_a_sp = {n for n in remaining_sps if TEST_TENANT_ID in next(iter(n))}
    assert len(remaining_a_sp) == 0, f"Expected 0, got: {remaining_a_sp}"

    # Tenant B's nodes survive
    remaining_b_lic = {
        n for n in remaining_licenses if TEST_TENANT_ID_B in next(iter(n))
    }
    assert len(remaining_b_lic) == 2, f"Expected 2, got: {remaining_b_lic}"

    remaining_b_sp = {n for n in remaining_sps if TEST_TENANT_ID_B in next(iter(n))}
    assert len(remaining_b_sp) == 4, f"Expected 4, got: {remaining_b_sp}"
