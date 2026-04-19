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
    Ensure that grants get loaded and effective access relationships are created.
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://fake.tailscale.com",
        "org": TEST_ORG,
    }
    _ensure_local_neo4j_has_test_tailnets(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Load devices first (needed for grant resolution)
    devices, _ = cartography.intel.tailscale.devices.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
    )

    # Load ACLs (groups, tags, postures, grants)
    postures, posture_conditions, grants, groups = (
        cartography.intel.tailscale.acls.sync(
            neo4j_session,
            api_session,
            common_job_parameters,
            TEST_ORG,
            tests.data.tailscale.users.TAILSCALE_USERS,
        )
    )

    # Act: sync grants
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

    # Assert: Grant nodes exist
    expected_grant_nodes = {
        ("grant:0",),
        ("grant:1",),
        ("grant:2",),
    }
    assert check_nodes(neo4j_session, "TailscaleGrant", ["id"]) == expected_grant_nodes

    # Assert: Grant to Tailnet relationships exist
    expected_rels = {
        ("grant:0", TEST_ORG),
        ("grant:1", TEST_ORG),
        ("grant:2", TEST_ORG),
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

    # Assert: Grant SOURCE relationships from groups
    # grant:0 has source group:example
    # grant:2 has source autogroup:member
    expected_source_group_rels = {
        ("group:example", "grant:0"),
        ("autogroup:member", "grant:2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleGroup",
            "id",
            "TailscaleGrant",
            "id",
            "SOURCE",
            rel_direction_right=True,
        )
        == expected_source_group_rels
    )

    # Assert: Grant SOURCE relationships from users
    # grant:1 has source mbsimpson@simpson.corp
    expected_source_user_rels = {
        ("123456", "grant:1"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleUser",
            "id",
            "TailscaleGrant",
            "id",
            "SOURCE",
            rel_direction_right=True,
        )
        == expected_source_user_rels
    )

    # Assert: Grant DESTINATION relationships to tags
    # grant:0 and grant:2 have destination tag:byod
    expected_dest_tag_rels = {
        ("grant:0", "tag:byod"),
        ("grant:2", "tag:byod"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleGrant",
            "id",
            "TailscaleTag",
            "id",
            "DESTINATION",
            rel_direction_right=True,
        )
        == expected_dest_tag_rels
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
def test_tailscale_grants_effective_access(
    mock_attrs,
    mock_devices,
    mock_acls,
    neo4j_session,
):
    """
    Ensure that effective access (CAN_ACCESS) relationships are resolved correctly.
    """

    # Arrange
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

    # Load ACLs
    postures, posture_conditions, grants, groups = (
        cartography.intel.tailscale.acls.sync(
            neo4j_session,
            api_session,
            common_job_parameters,
            TEST_ORG,
            tests.data.tailscale.users.TAILSCALE_USERS,
        )
    )

    # Act: sync grants
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

    # Assert: User CAN_ACCESS relationships
    # grant:0: group:example (hjsimpson) -> tag:byod (device p892kg92CNTRL)
    # grant:1: mbsimpson -> * (all 4 devices)
    # grant:2: autogroup:member (mbsimpson, hjsimpson) -> tag:byod (device p892kg92CNTRL)
    # After dedup, user access should be:
    # - hjsimpson -> p892kg92CNTRL (via grant:0, group:example member)
    # - mbsimpson -> all 4 devices (via grant:1, direct user)
    expected_user_access = {
        ("654321", "p892kg92CNTRL"),  # hjsimpson via grant:0 (group:example)
        ("123456", "p892kg92CNTRL"),  # mbsimpson via grant:1 (wildcard)
        ("123456", "n292kg92CNTRL"),  # mbsimpson via grant:1 (wildcard)
        ("123456", "n2fskgfgCNT89"),  # mbsimpson via grant:1 (wildcard)
        ("123456", "abcskgfgCN789"),  # mbsimpson via grant:1 (wildcard)
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

    # Assert: Group CAN_ACCESS relationships
    # grant:0: group:example -> tag:byod (device p892kg92CNTRL)
    # grant:2: autogroup:member -> tag:byod (device p892kg92CNTRL)
    expected_group_access = {
        ("group:example", "p892kg92CNTRL"),
        ("autogroup:member", "p892kg92CNTRL"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleGroup",
            "id",
            "TailscaleDevice",
            "id",
            "CAN_ACCESS",
            rel_direction_right=True,
        )
        == expected_group_access
    )
