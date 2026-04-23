from unittest.mock import patch

import pytest

import cartography.intel.microsoft.intune.compliance_policies
import cartography.intel.microsoft.intune.detected_apps
import cartography.intel.microsoft.intune.managed_devices
from cartography.intel.microsoft.intune.compliance_policies import (
    sync_compliance_policies,
)
from cartography.intel.microsoft.intune.detected_apps import sync_detected_apps
from cartography.intel.microsoft.intune.managed_devices import sync_managed_devices
from cartography.intel.microsoft.intune.reports import ExportedReportRows
from cartography.util import run_scoped_analysis_job
from tests.data.microsoft.intune.compliance_policies import MOCK_COMPLIANCE_POLICIES
from tests.data.microsoft.intune.compliance_policies import TEST_GROUP_ID
from tests.data.microsoft.intune.detected_apps import MOCK_DETECTED_APP_AGGREGATE_ROWS
from tests.data.microsoft.intune.detected_apps import MOCK_DETECTED_APP_RAW_ROWS
from tests.data.microsoft.intune.managed_devices import MOCK_MANAGED_DEVICES
from tests.data.microsoft.intune.managed_devices import TEST_TENANT_ID
from tests.data.microsoft.intune.managed_devices import TEST_USER_ID_1
from tests.data.microsoft.intune.managed_devices import TEST_USER_ID_2
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 1234567890
APP_KEY_DEVICE_INVENTORY_AGENT = "0142ec1846a5fe5aae49d155590a2116300000904abcd"
APP_KEY_CHROME = "4f5cf2a0a1c0f5b9d4601f6ca58f5a0c9b5d77e11c1f"
APP_KEY_CURSOR = "75c4c0a1f23d4e5b98aa1274c1e0dbbb73f0fffeabcd"
APP_KEY_TAILSCALE = "da8ab4f0d2cfe2bb9486778d6a628673da7a6e20b1dd"


async def _mock_get_managed_devices(client):
    for device in MOCK_MANAGED_DEVICES:
        yield device


async def _mock_get_detected_app_aggregate_rows(client):
    return ExportedReportRows(
        fieldnames=(
            "ApplicationKey",
            "ApplicationId",
            "ApplicationName",
            "ApplicationPublisher",
            "ApplicationVersion",
            "DeviceCount",
            "Platform",
        ),
        rows=MOCK_DETECTED_APP_AGGREGATE_ROWS,
    )


async def _mock_get_detected_app_raw_rows(client):
    return ExportedReportRows(
        fieldnames=(
            "ApplicationKey",
            "ApplicationName",
            "ApplicationPublisher",
            "ApplicationVersion",
            "Platform",
            "DeviceId",
        ),
        rows=MOCK_DETECTED_APP_RAW_ROWS,
    )


async def _mock_get_compliance_policies(client):
    for policy in MOCK_COMPLIANCE_POLICIES:
        yield policy


def _create_prereq_nodes(neo4j_session):
    """Create prerequisite nodes that the Intune module depends on."""
    neo4j_session.run(
        "MERGE (t:AzureTenant:EntraTenant {id: $id}) SET t.display_name = $name",
        id=TEST_TENANT_ID,
        name="Test Tenant",
    )
    neo4j_session.run(
        "MERGE (u:EntraUser {id: $id}) SET u.user_principal_name = $upn",
        id=TEST_USER_ID_1,
        upn="shyam@example.test",
    )
    neo4j_session.run(
        "MERGE (u:EntraUser {id: $id}) SET u.user_principal_name = $upn",
        id=TEST_USER_ID_2,
        upn="testuser@example.test",
    )
    neo4j_session.run(
        "MERGE (g:EntraGroup {id: $id}) SET g.display_name = $name",
        id=TEST_GROUP_ID,
        name="All Users",
    )
    neo4j_session.run(
        "MATCH (u:EntraUser {id: $uid}), (g:EntraGroup {id: $gid}) MERGE (u)-[:MEMBER_OF]->(g)",
        uid=TEST_USER_ID_1,
        gid=TEST_GROUP_ID,
    )
    neo4j_session.run(
        "MATCH (u:EntraUser {id: $uid}), (g:EntraGroup {id: $gid}) MERGE (u)-[:MEMBER_OF]->(g)",
        uid=TEST_USER_ID_2,
        gid=TEST_GROUP_ID,
    )


@patch.object(
    cartography.intel.microsoft.intune.managed_devices,
    "get_managed_devices",
    side_effect=_mock_get_managed_devices,
)
@patch.object(
    cartography.intel.microsoft.intune.detected_apps,
    "get_detected_app_aggregate_rows",
    side_effect=_mock_get_detected_app_aggregate_rows,
)
@patch.object(
    cartography.intel.microsoft.intune.detected_apps,
    "get_detected_app_raw_rows",
    side_effect=_mock_get_detected_app_raw_rows,
)
@patch.object(
    cartography.intel.microsoft.intune.compliance_policies,
    "get_compliance_policies",
    side_effect=_mock_get_compliance_policies,
)
@pytest.mark.asyncio
async def test_sync_intune(
    mock_compliance_policies,
    mock_detected_app_raw_rows,
    mock_detected_app_aggregate_rows,
    mock_managed_devices,
    neo4j_session,
):
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID}
    _create_prereq_nodes(neo4j_session)

    await sync_managed_devices(
        neo4j_session,
        None,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    await sync_detected_apps(
        neo4j_session,
        None,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    await sync_compliance_policies(
        neo4j_session,
        None,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session, "IntuneManagedDevice", ["id", "device_name", "compliance_state"]
    ) == {
        ("device-001", "Shyam's MacBook Pro", "compliant"),
        ("device-002", "Test Windows Laptop", "noncompliant"),
    }

    assert check_rels(
        neo4j_session,
        "EntraUser",
        "id",
        "IntuneManagedDevice",
        "id",
        "ENROLLED_TO",
    ) == {
        (TEST_USER_ID_1, "device-001"),
        (TEST_USER_ID_2, "device-002"),
    }

    assert check_nodes(neo4j_session, "IntuneDetectedApp", ["id", "display_name"]) == {
        (APP_KEY_DEVICE_INVENTORY_AGENT, "Microsoft Device Inventory Agent"),
        (APP_KEY_CHROME, "Google Chrome"),
        (APP_KEY_CURSOR, "Cursor (User)"),
        (APP_KEY_TAILSCALE, "Tailscale"),
    }

    assert check_rels(
        neo4j_session,
        "IntuneManagedDevice",
        "id",
        "IntuneDetectedApp",
        "id",
        "HAS_APP",
    ) == {
        ("device-001", APP_KEY_CHROME),
        ("device-002", APP_KEY_CHROME),
        ("device-002", APP_KEY_DEVICE_INVENTORY_AGENT),
        ("device-001", APP_KEY_TAILSCALE),
    }

    assert check_nodes(
        neo4j_session, "IntuneCompliancePolicy", ["id", "display_name", "platform"]
    ) == {
        ("policy-001", "macOS Compliance Policy", "macOS"),
        ("policy-002", "Android Compliance Policy", "android"),
    }

    assert check_rels(
        neo4j_session,
        "IntuneCompliancePolicy",
        "id",
        "EntraGroup",
        "id",
        "ASSIGNED_TO",
    ) == {
        ("policy-001", TEST_GROUP_ID),
    }

    assert check_rels(
        neo4j_session,
        "IntuneManagedDevice",
        "id",
        "EntraTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("device-001", TEST_TENANT_ID),
        ("device-002", TEST_TENANT_ID),
    }

    assert check_rels(
        neo4j_session,
        "IntuneDetectedApp",
        "id",
        "EntraTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (APP_KEY_DEVICE_INVENTORY_AGENT, TEST_TENANT_ID),
        (APP_KEY_CHROME, TEST_TENANT_ID),
        (APP_KEY_CURSOR, TEST_TENANT_ID),
        (APP_KEY_TAILSCALE, TEST_TENANT_ID),
    }

    assert check_rels(
        neo4j_session,
        "IntuneCompliancePolicy",
        "id",
        "EntraTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("policy-001", TEST_TENANT_ID),
        ("policy-002", TEST_TENANT_ID),
    }

    run_scoped_analysis_job(
        "intune_compliance_policy_device.json",
        neo4j_session,
        common_job_parameters,
    )

    assert check_rels(
        neo4j_session,
        "IntuneCompliancePolicy",
        "id",
        "IntuneManagedDevice",
        "id",
        "APPLIES_TO",
    ) == {
        ("policy-001", "device-001"),
        ("policy-001", "device-002"),
        ("policy-002", "device-001"),
        ("policy-002", "device-002"),
    }
