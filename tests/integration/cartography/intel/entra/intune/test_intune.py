from unittest.mock import patch

import pytest

import cartography.intel.entra.intune.compliance_policies
import cartography.intel.entra.intune.detected_apps
import cartography.intel.entra.intune.managed_devices
from cartography.intel.entra.intune.compliance_policies import sync_compliance_policies
from cartography.intel.entra.intune.detected_apps import sync_detected_apps
from cartography.intel.entra.intune.managed_devices import sync_managed_devices
from tests.data.intune.compliance_policies import MOCK_COMPLIANCE_POLICIES
from tests.data.intune.compliance_policies import TEST_GROUP_ID
from tests.data.intune.detected_apps import MOCK_DETECTED_APPS
from tests.data.intune.managed_devices import MOCK_MANAGED_DEVICES
from tests.data.intune.managed_devices import TEST_TENANT_ID
from tests.data.intune.managed_devices import TEST_USER_ID_1
from tests.data.intune.managed_devices import TEST_USER_ID_2
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 1234567890


async def _mock_get_managed_devices(client):
    for device in MOCK_MANAGED_DEVICES:
        yield device


async def _mock_get_detected_apps(client):
    for app in MOCK_DETECTED_APPS:
        yield app


async def _mock_get_compliance_policies(client):
    for policy in MOCK_COMPLIANCE_POLICIES:
        yield policy


def _create_prereq_nodes(neo4j_session):
    """Create prerequisite nodes that the Intune module depends on."""
    # Create EntraTenant node (normally created by the Entra module)
    neo4j_session.run(
        "MERGE (t:AzureTenant:EntraTenant {id: $id}) SET t.display_name = $name",
        id=TEST_TENANT_ID,
        name="Test Tenant",
    )

    # Create EntraUser nodes
    neo4j_session.run(
        "MERGE (u:EntraUser {id: $id}) SET u.user_principal_name = $upn",
        id=TEST_USER_ID_1,
        upn="shyam@subimage.io",
    )
    neo4j_session.run(
        "MERGE (u:EntraUser {id: $id}) SET u.user_principal_name = $upn",
        id=TEST_USER_ID_2,
        upn="testuser@subimage.io",
    )

    # Create EntraGroup node
    neo4j_session.run(
        "MERGE (g:EntraGroup {id: $id}) SET g.display_name = $name",
        id=TEST_GROUP_ID,
        name="All Users",
    )


@patch.object(
    cartography.intel.entra.intune.managed_devices,
    "get_managed_devices",
    side_effect=_mock_get_managed_devices,
)
@patch.object(
    cartography.intel.entra.intune.detected_apps,
    "get_detected_apps",
    side_effect=_mock_get_detected_apps,
)
@patch.object(
    cartography.intel.entra.intune.compliance_policies,
    "get_compliance_policies",
    side_effect=_mock_get_compliance_policies,
)
@pytest.mark.asyncio
async def test_sync_intune(
    mock_compliance_policies,
    mock_detected_apps,
    mock_managed_devices,
    neo4j_session,
):
    # Arrange
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID}
    _create_prereq_nodes(neo4j_session)

    # Act
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

    # Assert: managed devices exist
    assert check_nodes(
        neo4j_session, "IntuneManagedDevice", ["id", "device_name", "compliance_state"]
    ) == {
        ("device-001", "Shyam's MacBook Pro", "compliant"),
        ("device-002", "Test Windows Laptop", "noncompliant"),
    }

    # Assert: ENROLLED_TO relationship between EntraUser and IntuneManagedDevice
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

    # Assert: detected apps exist
    assert check_nodes(neo4j_session, "IntuneDetectedApp", ["id", "display_name"]) == {
        ("app-001", "Google Chrome"),
        ("app-002", "Tailscale"),
    }

    # Assert: HAS_APP relationship between IntuneManagedDevice and IntuneDetectedApp
    assert check_rels(
        neo4j_session,
        "IntuneManagedDevice",
        "id",
        "IntuneDetectedApp",
        "id",
        "HAS_APP",
    ) == {
        ("device-001", "app-001"),
        ("device-002", "app-001"),
        ("device-001", "app-002"),
    }

    # Assert: compliance policies exist
    assert check_nodes(
        neo4j_session, "IntuneCompliancePolicy", ["id", "display_name", "platform"]
    ) == {
        ("policy-001", "macOS Compliance Policy", "macOS"),
        ("policy-002", "Android Compliance Policy", "android"),
    }

    # Assert: ASSIGNED_TO relationship between IntuneCompliancePolicy and EntraGroup
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
