"""
Integration tests for Proxmox access control sync.
"""
from typing import Any
from unittest.mock import patch

import cartography.intel.proxmox.access
from tests.data.proxmox.access import MOCK_ACL_DATA
from tests.data.proxmox.access import MOCK_GROUP_DATA
from tests.data.proxmox.access import MOCK_ROLE_DATA
from tests.data.proxmox.access import MOCK_USER_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(cartography.intel.proxmox.access, "get_users", return_value=MOCK_USER_DATA)
@patch.object(cartography.intel.proxmox.access, "get_groups", return_value=MOCK_GROUP_DATA)
@patch.object(cartography.intel.proxmox.access, "get_roles", return_value=MOCK_ROLE_DATA)
@patch.object(cartography.intel.proxmox.access, "get_acls", return_value=MOCK_ACL_DATA)
def test_sync_access_control(mock_get_acls, mock_get_roles, mock_get_groups, mock_get_users, neo4j_session):
    """
    Test that access control (users, groups, roles, ACLs) sync correctly.
    """
    # Arrange
    common_job_parameters: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Create cluster first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id,
            c.lastupdated = $update_tag
        """,
        cluster_id=TEST_CLUSTER_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.proxmox.access.sync(
        neo4j_session,
        None,  # proxmox_client mocked
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Users exist
    expected_users = {
        ("root@pam", "root@example.com"),
        ("admin@pve", "admin@example.com"),
        ("readonly@pam", "readonly@example.com"),
        ("disabled@pam", "disabled@example.com"),
    }
    assert check_nodes(neo4j_session, "ProxmoxUser", ["id", "email"]) == expected_users

    # Assert - Groups exist
    expected_groups = {
        ("admins", "Administrator group"),
        ("operators", "Operator group"),
        ("auditors", "Read-only auditor group"),
    }
    assert check_nodes(neo4j_session, "ProxmoxGroup", ["id", "comment"]) == expected_groups

    # Assert - Roles exist
    expected_roles = {
        ("Administrator", True),
        ("PVEAuditor", True),
        ("CustomRole", False),
    }
    assert check_nodes(neo4j_session, "ProxmoxRole", ["id", "special"]) == expected_roles

    # Assert - ACLs exist
    result = neo4j_session.run(
        """
        MATCH (acl:ProxmoxACL)
        RETURN count(acl) as count
        """
    )
    assert result.single()["count"] == 4

    # Assert - User to cluster relationships
    expected_user_rels = {
        ("root@pam", TEST_CLUSTER_ID),
        ("admin@pve", TEST_CLUSTER_ID),
        ("readonly@pam", TEST_CLUSTER_ID),
        ("disabled@pam", TEST_CLUSTER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxUser",
            "id",
            "ProxmoxCluster",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_user_rels
    )

    # Assert - User to group relationships
    result = neo4j_session.run(
        """
        MATCH (u:ProxmoxUser)-[:MEMBER_OF_GROUP]->(g:ProxmoxGroup)
        RETURN u.userid as userid, g.groupid as groupid
        ORDER BY userid, groupid
        """
    )
    user_group_rels = [(r["userid"], r["groupid"]) for r in result]
    assert user_group_rels == [
        ("admin@pve", "admins"),
        ("readonly@pam", "auditors"),
        ("root@pam", "admins"),
        ("root@pam", "operators"),
    ]

    # Assert - ACL to role relationships
    result = neo4j_session.run(
        """
        MATCH (acl:ProxmoxACL)-[:GRANTS_ROLE]->(r:ProxmoxRole)
        RETURN acl.path as path, r.roleid as roleid
        ORDER BY path, roleid
        """
    )
    acl_role_rels = [(r["path"], r["roleid"]) for r in result]
    assert acl_role_rels == [
        ("/", "Administrator"),
        ("/", "Administrator"),
        ("/vms", "PVEAuditor"),
        ("/vms/100", "CustomRole"),
    ]

    # Assert - ACL to user relationships
    result = neo4j_session.run(
        """
        MATCH (acl:ProxmoxACL)-[:APPLIES_TO_USER]->(u:ProxmoxUser)
        RETURN acl.path as path, u.userid as userid
        ORDER BY path, userid
        """
    )
    acl_user_rels = [(r["path"], r["userid"]) for r in result]
    assert acl_user_rels == [
        ("/", "root@pam"),
        ("/vms/100", "readonly@pam"),
    ]

    # Assert - ACL to group relationships
    result = neo4j_session.run(
        """
        MATCH (acl:ProxmoxACL)-[:APPLIES_TO_GROUP]->(g:ProxmoxGroup)
        RETURN acl.path as path, g.groupid as groupid
        ORDER BY path, groupid
        """
    )
    acl_group_rels = [(r["path"], r["groupid"]) for r in result]
    assert acl_group_rels == [
        ("/", "admins"),
        ("/vms", "auditors"),
    ]

    # Assert - User properties
    result = neo4j_session.run(
        """
        MATCH (u:ProxmoxUser {userid: 'root@pam'})
        RETURN u.enable as enable, u.firstname as firstname
        """
    )
    user_props = result.single()
    assert user_props["enable"] is True
    assert user_props["firstname"] == "Root"
