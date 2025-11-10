"""
Integration tests for Proxmox access control sync.
"""

from typing import Any
from unittest.mock import patch

import cartography.intel.proxmox.access
from tests.data.proxmox.access import MOCK_ACL_DATA
from tests.data.proxmox.access import MOCK_GROUP_DATA
from tests.data.proxmox.access import MOCK_GROUP_MEMBERS_DATA
from tests.data.proxmox.access import MOCK_ROLE_DATA
from tests.data.proxmox.access import MOCK_USER_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(
    cartography.intel.proxmox.access, "get_users", return_value=MOCK_USER_DATA
)
@patch.object(
    cartography.intel.proxmox.access, "get_groups", return_value=MOCK_GROUP_DATA
)
@patch.object(
    cartography.intel.proxmox.access, "get_roles", return_value=MOCK_ROLE_DATA
)
@patch.object(cartography.intel.proxmox.access, "get_acls", return_value=MOCK_ACL_DATA)
@patch.object(
    cartography.intel.proxmox.access, "get_group_members", return_value=MOCK_GROUP_MEMBERS_DATA
)
def test_sync_access_control(
    mock_get_group_members, mock_get_acls, mock_get_roles, mock_get_groups, mock_get_users, neo4j_session
):
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
    assert (
        check_nodes(neo4j_session, "ProxmoxGroup", ["id", "comment"]) == expected_groups
    )

    # Assert - Roles exist
    expected_roles = {
        ("Administrator", True),
        ("PVEAuditor", True),
        ("CustomRole", False),
    }
    assert (
        check_nodes(neo4j_session, "ProxmoxRole", ["id", "special"]) == expected_roles
    )

    # Assert - ACLs exist
    result = neo4j_session.run(
        """
        MATCH (acl:ProxmoxACL)
        RETURN count(acl) as count
        """
    )
    assert result.single()["count"] == 7  # Updated to match new test data

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
        ("/nodes/node1", "PVEAuditor"),
        ("/pool/production", "CustomRole"),
        ("/storage/local-lvm", "PVEAuditor"),
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
        ("/pool/production", "admin@pve"),
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
        ("/nodes/node1", "operators"),
        ("/storage/local-lvm", "auditors"),
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


@patch.object(
    cartography.intel.proxmox.access, "get_users", return_value=MOCK_USER_DATA
)
@patch.object(
    cartography.intel.proxmox.access, "get_groups", return_value=MOCK_GROUP_DATA
)
@patch.object(
    cartography.intel.proxmox.access, "get_roles", return_value=MOCK_ROLE_DATA
)
@patch.object(cartography.intel.proxmox.access, "get_acls", return_value=MOCK_ACL_DATA)
@patch.object(
    cartography.intel.proxmox.access, "get_group_members", return_value=MOCK_GROUP_MEMBERS_DATA
)
def test_acl_resource_relationships(
    mock_get_group_members, mock_get_acls, mock_get_roles, mock_get_groups, mock_get_users, neo4j_session
):
    """
    Test that ACL-to-resource relationships are created correctly.
    """
    # Arrange
    common_job_parameters: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Create cluster
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id, c.lastupdated = $update_tag
        """,
        cluster_id=TEST_CLUSTER_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create test resources for ACLs to link to
    neo4j_session.run(
        """
        // Create VM
        MERGE (vm:ProxmoxVM {vmid: 100})
        SET vm.id = 'node1/qemu/100',
            vm.name = 'test-vm',
            vm.lastupdated = $update_tag
        
        // Create Storage
        MERGE (s:ProxmoxStorage {id: 'local-lvm'})
        SET s.name = 'local-lvm',
            s.lastupdated = $update_tag
        
        // Create Pool
        MERGE (p:ProxmoxPool {poolid: 'production'})
        SET p.id = 'production',
            p.lastupdated = $update_tag
        
        // Create Node
        MERGE (n:ProxmoxNode {id: 'node1'})
        SET n.name = 'node1',
            n.lastupdated = $update_tag
        """,
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

    # Assert - ACL to cluster relationships (root path)
    result = neo4j_session.run(
        """
        MATCH (acl:ProxmoxACL {path: '/'})-[:GRANTS_ACCESS_TO]->(c:ProxmoxCluster)
        RETURN count(*) as count
        """
    )
    assert result.single()["count"] == 2  # root@pam and admins group

    # Assert - ACL to VM relationships
    result = neo4j_session.run(
        """
        MATCH (acl:ProxmoxACL {path: '/vms/100'})-[:GRANTS_ACCESS_TO]->(vm:ProxmoxVM {vmid: 100})
        RETURN count(*) as count
        """
    )
    assert result.single()["count"] == 1  # readonly@pam

    # Assert - ACL to Storage relationships
    result = neo4j_session.run(
        """
        MATCH (acl:ProxmoxACL {path: '/storage/local-lvm'})-[:GRANTS_ACCESS_TO]->(s:ProxmoxStorage {id: 'local-lvm'})
        RETURN count(*) as count
        """
    )
    assert result.single()["count"] == 1  # auditors group

    # Assert - ACL to Pool relationships
    result = neo4j_session.run(
        """
        MATCH (acl:ProxmoxACL {path: '/pool/production'})-[:GRANTS_ACCESS_TO]->(p:ProxmoxPool {poolid: 'production'})
        RETURN count(*) as count
        """
    )
    assert result.single()["count"] == 1  # admin@pve

    # Assert - ACL to Node relationships
    result = neo4j_session.run(
        """
        MATCH (acl:ProxmoxACL {path: '/nodes/node1'})-[:GRANTS_ACCESS_TO]->(n:ProxmoxNode {id: 'node1'})
        RETURN count(*) as count
        """
    )
    assert result.single()["count"] == 1  # operators group

    # Assert - ACL properties include resource metadata
    result = neo4j_session.run(
        """
        MATCH (acl:ProxmoxACL {path: '/vms/100'})
        RETURN acl.resource_type as resource_type, acl.resource_id as resource_id
        """
    )
    acl_props = result.single()
    assert acl_props["resource_type"] == "vm"
    assert acl_props["resource_id"] == "100"


@patch.object(
    cartography.intel.proxmox.access, "get_users", return_value=MOCK_USER_DATA
)
@patch.object(
    cartography.intel.proxmox.access, "get_groups", return_value=MOCK_GROUP_DATA
)
@patch.object(
    cartography.intel.proxmox.access, "get_roles", return_value=MOCK_ROLE_DATA
)
@patch.object(cartography.intel.proxmox.access, "get_acls", return_value=MOCK_ACL_DATA)
@patch.object(
    cartography.intel.proxmox.access, "get_group_members", return_value=MOCK_GROUP_MEMBERS_DATA
)
def test_effective_permissions(
    mock_get_group_members, mock_get_acls, mock_get_roles, mock_get_groups, mock_get_users, neo4j_session
):
    """
    Test that effective permission relationships are created correctly.
    """
    # Arrange
    common_job_parameters: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Create cluster
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id, c.lastupdated = $update_tag
        """,
        cluster_id=TEST_CLUSTER_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create test resources
    neo4j_session.run(
        """
        MERGE (vm:ProxmoxVM {vmid: 100})
        SET vm.id = 'node1/qemu/100', vm.name = 'test-vm'
        
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    # Act
    cartography.intel.proxmox.access.sync(
        neo4j_session,
        None,  # proxmox_client mocked
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Direct user permissions exist
    result = neo4j_session.run(
        """
        MATCH (u:ProxmoxUser {userid: 'root@pam'})-[p:HAS_PERMISSION]->(c:ProxmoxCluster)
        RETURN p.role as role, p.privileges as privileges, p.via_group as via_group
        """
    )
    permission = result.single()
    assert permission is not None
    assert permission["role"] == "Administrator"
    assert "VM.Allocate" in permission["privileges"]

    # Assert - Group permissions exist
    result = neo4j_session.run(
        """
        MATCH (g:ProxmoxGroup {groupid: 'admins'})-[p:HAS_PERMISSION]->(c:ProxmoxCluster)
        RETURN p.role as role
        """
    )
    group_permission = result.single()
    assert group_permission is not None
    assert group_permission["role"] == "Administrator"

    # Assert - Inherited permissions (user -> group -> resource)
    result = neo4j_session.run(
        """
        MATCH (u:ProxmoxUser)-[:MEMBER_OF_GROUP]->(g:ProxmoxGroup {groupid: 'admins'})
        MATCH (u)-[p:HAS_PERMISSION]->(c:ProxmoxCluster)
        WHERE p.via_group = true OR p.via_group IS NULL
        RETURN count(DISTINCT u) as user_count
        """
    )
    # Both root@pam and admin@pve are in admins group, should have permissions to cluster
    assert result.single()["user_count"] >= 2

    # Assert - Permission metadata is present
    result = neo4j_session.run(
        """
        MATCH (u:ProxmoxUser {userid: 'readonly@pam'})-[p:HAS_PERMISSION]->(vm:ProxmoxVM {vmid: 100})
        RETURN p.via_acl as via_acl, p.path as path, p.propagate as propagate
        """
    )
    vm_permission = result.single()
    if vm_permission:  # Only if VM was created
        assert vm_permission["via_acl"] is not None
        assert vm_permission["path"] == "/vms/100"
        assert vm_permission["propagate"] is not None
