from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.jamf.computers
import cartography.intel.jamf.groups
import cartography.intel.jamf.mobile_devices
from cartography.intel.jamf.computers import sync as sync_computers
from cartography.intel.jamf.groups import sync as sync_groups
from cartography.intel.jamf.mobile_devices import sync as sync_mobile_devices
from tests.data.jamf.computers import COMPUTERS
from tests.data.jamf.groups import GROUPS
from tests.data.jamf.mobile_devices import MOBILE_DEVICES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JAMF_URI = "https://test.jamfcloud.com"


@patch.object(cartography.intel.jamf.groups, "get", return_value=GROUPS)
def test_sync_groups(mock_get, neo4j_session):
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_JAMF_URI,
    }

    sync_groups(
        neo4j_session,
        MagicMock(),
        TEST_JAMF_URI,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_nodes(neo4j_session, "JamfTenant", ["id"]) == {
        (TEST_JAMF_URI,),
    }

    assert check_nodes(
        neo4j_session,
        "JamfComputerGroup",
        ["id", "name", "description", "membership_count", "is_smart"],
    ) == {
        (101, "Springfield Managed Macs", "All managed macOS endpoints", 42, True),
        (102, "Sector 7G Workstations", "Power plant engineering fleet", 12, False),
    }

    assert check_nodes(
        neo4j_session,
        "JamfMobileDeviceGroup",
        ["id", "name", "description", "membership_count", "is_smart"],
    ) == {
        (201, "Springfield iPhones", "Managed iPhone fleet", 85, True),
        (202, "Springfield iPads", "Managed iPad fleet", 19, True),
    }

    assert check_rels(
        neo4j_session,
        "JamfTenant",
        "id",
        "JamfComputerGroup",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_JAMF_URI, 101),
        (TEST_JAMF_URI, 102),
    }

    assert check_rels(
        neo4j_session,
        "JamfTenant",
        "id",
        "JamfMobileDeviceGroup",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_JAMF_URI, 201),
        (TEST_JAMF_URI, 202),
    }


@patch.object(cartography.intel.jamf.groups, "get", return_value=GROUPS)
@patch.object(cartography.intel.jamf.computers, "get", return_value=COMPUTERS)
def test_sync_computers(mock_get, mock_groups_get, neo4j_session):
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_JAMF_URI,
    }

    sync_groups(
        neo4j_session,
        MagicMock(),
        TEST_JAMF_URI,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    sync_computers(
        neo4j_session,
        MagicMock(),
        TEST_JAMF_URI,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "JamfComputer",
        [
            "id",
            "name",
            "serial_number",
            "os_version",
            "firewall_enabled",
            "filevault_enabled",
            "username",
        ],
    ) == {
        (
            7001,
            "Springfield-Admin-Mac-01",
            "C02SPRING001",
            "14.5",
            True,
            True,
            "h.simpson",
        ),
        (
            7002,
            "Springfield-Design-Mac-02",
            "C02SPRING002",
            "13.6.7",
            False,
            False,
            "l.simpson",
        ),
    }

    assert check_rels(
        neo4j_session,
        "JamfTenant",
        "id",
        "JamfComputer",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_JAMF_URI, 7001),
        (TEST_JAMF_URI, 7002),
    }

    assert check_rels(
        neo4j_session,
        "JamfComputer",
        "id",
        "JamfComputerGroup",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (7001, 101),
        (7001, 102),
        (7002, 101),
    }


@patch.object(
    cartography.intel.jamf.groups,
    "get",
    return_value=GROUPS,
)
@patch.object(
    cartography.intel.jamf.mobile_devices,
    "get",
    return_value=MOBILE_DEVICES,
)
def test_sync_mobile_devices(mock_get, mock_groups_get, neo4j_session):
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_JAMF_URI,
    }

    sync_groups(
        neo4j_session,
        MagicMock(),
        TEST_JAMF_URI,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    sync_mobile_devices(
        neo4j_session,
        MagicMock(),
        TEST_JAMF_URI,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "JamfMobileDevice",
        [
            "id",
            "display_name",
            "serial_number",
            "os",
            "platform",
            "passcode_compliant",
            "username",
        ],
    ) == {
        (
            9001,
            "Bart-iPhone-01",
            "IPHONESPRING001",
            "iOS",
            "iPhone",
            True,
            "b.simpson",
        ),
        (
            9002,
            "Lisa-iPad-01",
            "IPADSPRING001",
            "iPadOS",
            "iPad",
            False,
            "l.simpson",
        ),
    }

    assert check_rels(
        neo4j_session,
        "JamfTenant",
        "id",
        "JamfMobileDevice",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_JAMF_URI, 9001),
        (TEST_JAMF_URI, 9002),
    }

    assert check_rels(
        neo4j_session,
        "JamfMobileDevice",
        "id",
        "JamfMobileDeviceGroup",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (9001, 201),
    }
