from unittest.mock import patch

import requests

import cartography.intel.tailscale.acls
import cartography.intel.tailscale.devices
import cartography.intel.tailscale.grants
import tests.data.tailscale.devicepostureattributes
import tests.data.tailscale.devices
import tests.data.tailscale.grants
import tests.data.tailscale.users
from tests.integration.cartography.intel.tailscale.test_tailnets import (
    _ensure_local_neo4j_has_test_tailnets,
)
from tests.integration.cartography.intel.tailscale.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG = "simpson.corp"


def _setup_grants_test(neo4j_session):
    """Helper to set up the full grants test environment."""
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://fake.tailscale.com",
        "org": TEST_ORG,
    }
    _ensure_local_neo4j_has_test_tailnets(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Load devices
    devices, _ = cartography.intel.tailscale.devices.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
    )

    # Load ACLs (groups, tags, postures, grants + INHERITED_MEMBER_OF)
    postures, posture_conditions, grants, groups = (
        cartography.intel.tailscale.acls.sync(
            neo4j_session,
            api_session,
            common_job_parameters,
            TEST_ORG,
            tests.data.tailscale.users.TAILSCALE_USERS,
        )
    )

    # Sync grants
    cartography.intel.tailscale.grants.sync(
        neo4j_session,
        org=TEST_ORG,
        update_tag=TEST_UPDATE_TAG,
        grants=grants,
        devices=devices,
        groups=groups,
        tags=[],
        users=tests.data.tailscale.users.TAILSCALE_USERS,
    )

    return grants, groups, devices


@patch.object(
    cartography.intel.tailscale.acls,
    "get",
    return_value=tests.data.tailscale.grants.TAILSCALE_ACL_FILE_WITH_GRANTS,
)
@patch.object(
    cartography.intel.tailscale.devices,
    "get",
    return_value=tests.data.tailscale.devices.TAILSCALE_DEVICES,
)
@patch.object(
    cartography.intel.tailscale.devices,
    "get_device_posture_attributes",
    return_value=tests.data.tailscale.devicepostureattributes.TAILSCALE_DEVICE_POSTURE_ATTRIBUTES,
)
def test_load_tailscale_grants(mock_attrs, mock_devices, mock_acls, neo4j_session):
    """
    Ensure that grants get loaded and structural relationships are created.
    """
    _setup_grants_test(neo4j_session)

    # Assert: Grant nodes exist (5 grants in test data)
    expected_grant_nodes = {
        ("grant:0",),
        ("grant:1",),
        ("grant:2",),
        ("grant:3",),
        ("grant:4",),
    }
    assert check_nodes(neo4j_session, "TailscaleGrant", ["id"]) == expected_grant_nodes

    # Assert: Grant to Tailnet relationships exist
    expected_rels = {
        ("grant:0", TEST_ORG),
        ("grant:1", TEST_ORG),
        ("grant:2", TEST_ORG),
        ("grant:3", TEST_ORG),
        ("grant:4", TEST_ORG),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleGrant",
            "id",
            "TailscaleTailnet",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.tailscale.acls,
    "get",
    return_value=tests.data.tailscale.grants.TAILSCALE_ACL_FILE_WITH_GRANTS,
)
@patch.object(
    cartography.intel.tailscale.devices,
    "get",
    return_value=tests.data.tailscale.devices.TAILSCALE_DEVICES,
)
@patch.object(
    cartography.intel.tailscale.devices,
    "get_device_posture_attributes",
    return_value=tests.data.tailscale.devicepostureattributes.TAILSCALE_DEVICE_POSTURE_ATTRIBUTES,
)
def test_tailscale_grants_inherited_member_of(
    mock_attrs,
    mock_devices,
    mock_acls,
    neo4j_session,
):
    """
    Ensure that INHERITED_MEMBER_OF relationships are created in the graph
    for transitive sub-group membership (P1.2).

    group:employees contains group:corp as a sub-group.
    Users in group:corp should get INHERITED_MEMBER_OF -> group:employees.
    """
    _setup_grants_test(neo4j_session)

    # group:employees has sub_groups: ["group:corp"]
    # group:corp members: mbsimpson@simpson.corp, hjsimpson@simpson.corp
    # So both users should have INHERITED_MEMBER_OF -> group:employees
    expected_inherited = {
        ("123456", "group:employees"),  # mbsimpson
        ("654321", "group:employees"),  # hjsimpson
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleUser",
            "id",
            "TailscaleGroup",
            "id",
            "INHERITED_MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_inherited
    )


@patch.object(
    cartography.intel.tailscale.acls,
    "get",
    return_value=tests.data.tailscale.grants.TAILSCALE_ACL_FILE_WITH_GRANTS,
)
@patch.object(
    cartography.intel.tailscale.devices,
    "get",
    return_value=tests.data.tailscale.devices.TAILSCALE_DEVICES,
)
@patch.object(
    cartography.intel.tailscale.devices,
    "get_device_posture_attributes",
    return_value=tests.data.tailscale.devicepostureattributes.TAILSCALE_DEVICE_POSTURE_ATTRIBUTES,
)
def test_tailscale_grants_effective_user_access(
    mock_attrs,
    mock_devices,
    mock_acls,
    neo4j_session,
):
    """
    Ensure that effective user CAN_ACCESS relationships are resolved correctly,
    including autogroup:self (P1.3).
    """
    _setup_grants_test(neo4j_session)

    # Expected user CAN_ACCESS relationships:
    #
    # grant:0: group:example (hjsimpson) -> tag:byod (p892kg92CNTRL)
    # grant:1: mbsimpson -> * (all 4 devices)
    # grant:2: autogroup:member (mbsimpson, hjsimpson) -> tag:byod (p892kg92CNTRL)
    # grant:4: group:employees (direct members: none, but group:corp is sub-group)
    #   group:employees direct members = [] (only sub_groups)
    #   -> autogroup:self: no direct members to resolve
    #   (transitive resolution happens via INHERITED_MEMBER_OF in the graph,
    #    but grants.py only uses direct group members for CAN_ACCESS)
    #
    # After dedup:
    expected_user_access = {
        # hjsimpson via grant:0 (group:example -> tag:byod)
        ("654321", "p892kg92CNTRL"),
        # mbsimpson via grant:1 (wildcard dest)
        ("123456", "p892kg92CNTRL"),
        ("123456", "n292kg92CNTRL"),
        ("123456", "n2fskgfgCNT89"),
        ("123456", "abcskgfgCN789"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleUser",
            "id",
            "TailscaleDevice",
            "id",
            "CAN_ACCESS",
            rel_direction_right=True,
        )
        == expected_user_access
    )


@patch.object(
    cartography.intel.tailscale.acls,
    "get",
    return_value=tests.data.tailscale.grants.TAILSCALE_ACL_FILE_WITH_GRANTS,
)
@patch.object(
    cartography.intel.tailscale.devices,
    "get",
    return_value=tests.data.tailscale.devices.TAILSCALE_DEVICES,
)
@patch.object(
    cartography.intel.tailscale.devices,
    "get_device_posture_attributes",
    return_value=tests.data.tailscale.devicepostureattributes.TAILSCALE_DEVICE_POSTURE_ATTRIBUTES,
)
def test_tailscale_grants_device_to_device_access(
    mock_attrs,
    mock_devices,
    mock_acls,
    neo4j_session,
):
    """
    Ensure that device-to-device CAN_ACCESS relationships are resolved
    when a tag is used as a grant source (P1.1).
    """
    _setup_grants_test(neo4j_session)

    # grant:3: tag:byod -> * (all devices)
    # tag:byod devices: p892kg92CNTRL
    # So p892kg92CNTRL can access all other devices (excluding self)
    expected_device_access = {
        ("p892kg92CNTRL", "n292kg92CNTRL"),
        ("p892kg92CNTRL", "n2fskgfgCNT89"),
        ("p892kg92CNTRL", "abcskgfgCN789"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleDevice",
            "id",
            "TailscaleDevice",
            "id",
            "CAN_ACCESS",
            rel_direction_right=True,
        )
        == expected_device_access
    )
