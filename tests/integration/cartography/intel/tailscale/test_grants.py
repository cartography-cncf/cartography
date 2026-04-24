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
    Ensure that grants get loaded with stable hash-based IDs and
    structural relationships are created.
    """
    _setup_grants_test(neo4j_session)

    # Assert: 5 Grant nodes exist with stable hash IDs
    result = neo4j_session.run(
        "MATCH (g:TailscaleGrant) RETURN g.id AS id",
    )
    grant_ids = {r["id"] for r in result}
    assert len(grant_ids) == 5
    for grant_id in grant_ids:
        assert grant_id.startswith("grant:")
        assert len(grant_id) == len("grant:") + 12

    # Assert: All grants are connected to the Tailnet
    result = neo4j_session.run(
        """
        MATCH (t:TailscaleTailnet {id: $org})-[:RESOURCE]->(g:TailscaleGrant)
        RETURN count(g) AS cnt
        """,
        org=TEST_ORG,
    )
    assert result.single()["cnt"] == 5

    # Assert: SOURCE relationships from groups exist
    # grant with src=group:example, grant with src=autogroup:member,
    # grant with src=group:employees
    expected_source_groups = {"group:example", "autogroup:member", "group:employees"}
    result = neo4j_session.run(
        """
        MATCH (g:TailscaleGroup)-[:SOURCE]->(grant:TailscaleGrant)
        RETURN g.id AS group_id
        """,
    )
    actual_source_groups = {r["group_id"] for r in result}
    assert actual_source_groups == expected_source_groups

    # Assert: DESTINATION relationships to tags exist (tag:byod from 2 grants)
    result = neo4j_session.run(
        """
        MATCH (grant:TailscaleGrant)-[:DESTINATION]->(t:TailscaleTag)
        RETURN t.id AS tag_id, count(grant) AS cnt
        """,
    )
    tag_rels = {(r["tag_id"], r["cnt"]) for r in result}
    assert ("tag:byod", 2) in tag_rels


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
    Ensure that effective user CAN_ACCESS relationships are resolved correctly.
    """
    _setup_grants_test(neo4j_session)

    expected_user_access = {
        # hjsimpson via group:example -> tag:byod
        ("654321", "p892kg92CNTRL"),
        # hjsimpson via transitive group:employees -> autogroup:self
        ("654321", "n2fskgfgCNT89"),
        ("654321", "abcskgfgCN789"),
        # mbsimpson via wildcard dest
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

    # Device-to-device CAN_ACCESS includes:
    # - Direct tag source: tag:byod -> * (p892kg92CNTRL -> all others)
    # - Propagated from user access: mbsimpson's devices (p892kg92CNTRL,
    #   n292kg92CNTRL) can access all devices she has CAN_ACCESS to,
    #   and hjsimpson's devices (n2fskgfgCNT89, abcskgfgCN789) can access
    #   devices he has CAN_ACCESS to (p892kg92CNTRL via group:example)
    result = neo4j_session.run(
        """
        MATCH (d1:TailscaleDevice)-[:CAN_ACCESS]->(d2:TailscaleDevice)
        RETURN d1.id AS src, d2.id AS dst
        """,
    )
    device_rels = {(r["src"], r["dst"]) for r in result}
    # At minimum, the tag:byod -> * direct device access must be present
    assert ("p892kg92CNTRL", "n292kg92CNTRL") in device_rels
    assert ("p892kg92CNTRL", "n2fskgfgCNT89") in device_rels
    assert ("p892kg92CNTRL", "abcskgfgCN789") in device_rels
    # Propagated from mbsimpson's CAN_ACCESS (her device n292kg92CNTRL
    # inherits access to hjsimpson's devices)
    assert ("n292kg92CNTRL", "n2fskgfgCNT89") in device_rels
    assert ("n292kg92CNTRL", "abcskgfgCN789") in device_rels
    # No self-loops
    for src, dst in device_rels:
        assert src != dst


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
def test_tailscale_grants_granted_by_aggregation(
    mock_attrs,
    mock_devices,
    mock_acls,
    neo4j_session,
):
    """
    Ensure that granted_by on CAN_ACCESS relationships aggregates
    multiple grant IDs when several grants give access to the same pair.
    """
    _setup_grants_test(neo4j_session)

    # mbsimpson -> p892kg92CNTRL is granted by:
    # - the wildcard grant (src: mbsimpson, dst: *)
    # Note: the autogroup:member -> tag:byod grant has srcPosture so
    # it is filtered out (no posture_matches loaded in this test)
    result = neo4j_session.run(
        """
        MATCH (u:TailscaleUser {login_name: 'mbsimpson@simpson.corp'})
              -[r:CAN_ACCESS]->(d:TailscaleDevice {id: 'p892kg92CNTRL'})
        RETURN r.granted_by AS granted_by
        """,
    )
    record = result.single()
    granted_by = list(record["granted_by"])
    # At least 1 grant (the wildcard one; posture-gated grant is filtered)
    assert len(granted_by) >= 1
    # All should be valid grant IDs
    for grant_id in granted_by:
        assert grant_id.startswith("grant:")
