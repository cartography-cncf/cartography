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
    ]

    cluster_id = "test-cluster"
    result = transform_user_data(raw_users, cluster_id)

    assert len(result) == 2

    # Test root user
    root = next(u for u in result if u["userid"] == "root@pam")
    assert root["id"] == "root@pam"
    assert root["enable"] is True
    assert root["expire"] == 0
    assert root["firstname"] == "Root"
    assert root["lastname"] == "User"
    assert root["email"] == "root@example.com"
    assert root["groups"] == ["admins", "operators"]
    assert root["cluster_id"] == cluster_id

    # Test user with minimal fields
    test_user = next(u for u in result if u["userid"] == "test@pve")
    assert test_user["enable"] is False
    assert test_user["expire"] == 1735689600
    assert test_user["firstname"] is None
    assert test_user["groups"] == []


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
    ]

    cluster_id = "test-cluster"
    result = transform_acl_data(raw_acls, cluster_id)

    assert len(result) == 2

    # Test root ACL
    root_acl = next(a for a in result if a["ugid"] == "root@pam")
    assert root_acl["id"] == "/:root@pam:Administrator"
    assert root_acl["path"] == "/"
    assert root_acl["roleid"] == "Administrator"
    assert root_acl["propagate"] is True
    assert root_acl["cluster_id"] == cluster_id

    # Test group ACL
    group_acl = next(a for a in result if a["ugid"] == "auditors")
    assert group_acl["id"] == "/vms/100:auditors:PVEAuditor"
    assert group_acl["path"] == "/vms/100"
    assert group_acl["propagate"] is False
