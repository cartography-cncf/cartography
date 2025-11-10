"""
Tests for Proxmox access control module.
"""

from cartography.intel.proxmox.access import transform_acl_data
from cartography.intel.proxmox.access import transform_group_data
from cartography.intel.proxmox.access import transform_role_data
from cartography.intel.proxmox.access import transform_user_data


def test_transform_user_data():
    """Test user data transformation."""
    raw_users = [
        {
            "userid": "root@pam",
            "enable": 1,
            "expire": 0,
            "firstname": "Root",
            "lastname": "User",
            "email": "root@example.com",
            "comment": "Root user",
            "groups": "admins,operators",
        },
        {
            "userid": "test@pve",
            "enable": 0,
            "expire": 1735689600,
            "email": "test@example.com",
        },
        {
            "userid": "sso_user@entraid",
            "enable": 1,
            "expire": 0,
            "email": "sso@example.com",
            "comment": "SSO user",
            "groups": "",  # Empty groups for SSO users
        },
    ]

    group_members = {
        "admins": ["root@pam"],
        "operators": ["root@pam"],
        "sso_group": ["sso_user@entraid"],
    }

    cluster_id = "test-cluster"
    result = transform_user_data(raw_users, cluster_id, group_members)

    assert len(result) == 3

    # Test root user (groups from user data string)
    root = next(u for u in result if u["userid"] == "root@pam")
    assert root["id"] == "root@pam"
    assert root["enable"] is True
    assert root["expire"] == 0
    assert root["firstname"] == "Root"
    assert root["lastname"] == "User"
    assert root["email"] == "root@example.com"
    assert root["groups"] == ["admins", "operators"]
    assert root["cluster_id"] == cluster_id

    # Test user with minimal fields (no groups)
    test_user = next(u for u in result if u["userid"] == "test@pve")
    assert test_user["enable"] is False
    assert test_user["expire"] == 1735689600
    assert test_user["firstname"] is None
    assert test_user["groups"] == []

    # Test SSO user (groups enriched from group_members)
    sso_user = next(u for u in result if u["userid"] == "sso_user@entraid")
    assert sso_user["enable"] is True
    assert sso_user["groups"] == ["sso_group"]  # Enriched from group_members
    assert sso_user["email"] == "sso@example.com"


def test_transform_group_data():
    """Test group data transformation."""
    raw_groups = [
        {
            "groupid": "admins",
            "comment": "Administrator group",
        },
        {
            "groupid": "operators",
        },
    ]

    cluster_id = "test-cluster"
    result = transform_group_data(raw_groups, cluster_id)

    assert len(result) == 2

    # Test admins group
    admins = next(g for g in result if g["groupid"] == "admins")
    assert admins["id"] == "admins"
    assert admins["comment"] == "Administrator group"
    assert admins["cluster_id"] == cluster_id

    # Test group without comment
    operators = next(g for g in result if g["groupid"] == "operators")
    assert operators["comment"] is None


def test_transform_role_data():
    """Test role data transformation."""
    raw_roles = [
        {
            "roleid": "Administrator",
            "privs": "VM.Allocate,VM.Config,Sys.Modify",
            "special": 1,
        },
        {
            "roleid": "CustomRole",
            "privs": "VM.Audit",
            "special": 0,
        },
    ]

    cluster_id = "test-cluster"
    result = transform_role_data(raw_roles, cluster_id)

    assert len(result) == 2

    # Test Administrator role
    admin = next(r for r in result if r["roleid"] == "Administrator")
    assert admin["id"] == "Administrator"
    assert admin["privs"] == ["VM.Allocate", "VM.Config", "Sys.Modify"]
    assert admin["special"] is True
    assert admin["cluster_id"] == cluster_id

    # Test custom role
    custom = next(r for r in result if r["roleid"] == "CustomRole")
    assert custom["privs"] == ["VM.Audit"]
    assert custom["special"] is False


def test_transform_acl_data():
    """Test ACL data transformation."""
    raw_acls = [
        {
            "path": "/",
            "roleid": "Administrator",
            "ugid": "root@pam",
            "propagate": 1,
        },
        {
            "path": "/vms/100",
            "roleid": "PVEAuditor",
            "ugid": "auditors",
            "propagate": 0,
        },
        {
            "path": "/storage/local-lvm",
            "roleid": "CustomRole",
            "ugid": "admin@pve",
            "propagate": 1,
        },
        {
            "path": "/pool/production",
            "roleid": "PVEAuditor",
            "ugid": "operators",
            "propagate": 1,
        },
        {
            "path": "/nodes/node1",
            "roleid": "CustomRole",
            "ugid": "admin@pve",
            "propagate": 0,
        },
    ]

    cluster_id = "test-cluster"
    result = transform_acl_data(raw_acls, cluster_id)

    assert len(result) == 5

    # Test root ACL with cluster resource type
    root_acl = next(a for a in result if a["ugid"] == "root@pam")
    assert root_acl["id"] == "/:root@pam:Administrator"
    assert root_acl["path"] == "/"
    assert root_acl["roleid"] == "Administrator"
    assert root_acl["propagate"] is True
    assert root_acl["cluster_id"] == cluster_id
    assert root_acl["principal_type"] == "user"
    assert root_acl["resource_type"] == "cluster"
    assert root_acl["resource_id"] is None

    # Test group ACL with VM resource type
    group_acl = next(a for a in result if a["path"] == "/vms/100")
    assert group_acl["id"] == "/vms/100:auditors:PVEAuditor"
    assert group_acl["path"] == "/vms/100"
    assert group_acl["propagate"] is False
    assert group_acl["principal_type"] == "group"
    assert group_acl["resource_type"] == "vm"
    assert group_acl["resource_id"] == "100"

    # Test storage ACL
    storage_acl = next(a for a in result if a["path"] == "/storage/local-lvm")
    assert storage_acl["principal_type"] == "user"
    assert storage_acl["resource_type"] == "storage"
    assert storage_acl["resource_id"] == "local-lvm"

    # Test pool ACL
    pool_acl = next(a for a in result if a["path"] == "/pool/production")
    assert pool_acl["principal_type"] == "group"
    assert pool_acl["resource_type"] == "pool"
    assert pool_acl["resource_id"] == "production"

    # Test node ACL
    node_acl = next(a for a in result if a["path"] == "/nodes/node1")
    assert node_acl["principal_type"] == "user"
    assert node_acl["resource_type"] == "node"
    assert node_acl["resource_id"] == "node1"
