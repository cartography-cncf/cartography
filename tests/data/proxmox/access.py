"""
Mock data for Proxmox access control tests.
"""

MOCK_USER_DATA = [
    {
        "userid": "root@pam",
        "enable": 1,
        "expire": 0,
        "firstname": "Root",
        "lastname": "User",
        "email": "root@example.com",
        "comment": "Root user account",
        "groups": "admins,operators",
        "tokens": ["token1", "token2"],
    },
    {
        "userid": "admin@pve",
        "enable": 1,
        "expire": 0,
        "email": "admin@example.com",
        "comment": "Administrator account",
        "groups": "admins",
    },
    {
        "userid": "readonly@pam",
        "enable": 1,
        "expire": 1735689600,  # Future date
        "email": "readonly@example.com",
        "groups": "auditors",
    },
    {
        "userid": "disabled@pam",
        "enable": 0,
        "email": "disabled@example.com",
        "groups": "",
    },
]

MOCK_GROUP_DATA = [
    {
        "groupid": "admins",
        "comment": "Administrator group",
    },
    {
        "groupid": "operators",
        "comment": "Operator group",
    },
    {
        "groupid": "auditors",
        "comment": "Read-only auditor group",
    },
]

MOCK_ROLE_DATA = [
    {
        "roleid": "Administrator",
        "privs": "VM.Allocate,VM.Config,Sys.Modify,Datastore.Allocate",
        "special": 1,
    },
    {
        "roleid": "PVEAuditor",
        "privs": "VM.Audit,Sys.Audit,Datastore.Audit",
        "special": 1,
    },
    {
        "roleid": "CustomRole",
        "privs": "VM.Config,VM.PowerMgmt",
        "special": 0,
    },
]

MOCK_ACL_DATA = [
    {
        "path": "/",
        "roleid": "Administrator",
        "ugid": "root@pam",
        "propagate": 1,
    },
    {
        "path": "/",
        "roleid": "Administrator",
        "ugid": "admins",
        "propagate": 1,
    },
    {
        "path": "/vms",
        "roleid": "PVEAuditor",
        "ugid": "auditors",
        "propagate": 1,
    },
    {
        "path": "/vms/100",
        "roleid": "CustomRole",
        "ugid": "readonly@pam",
        "propagate": 0,
    },
    {
        "path": "/storage/local-lvm",
        "roleid": "PVEAuditor",
        "ugid": "auditors",
        "propagate": 1,
    },
    {
        "path": "/pool/production",
        "roleid": "CustomRole",
        "ugid": "admin@pve",
        "propagate": 1,
    },
    {
        "path": "/nodes/node1",
        "roleid": "PVEAuditor",
        "ugid": "operators",
        "propagate": 0,
    },
]

MOCK_GROUP_MEMBERS_DATA = {
    "admins": ["root@pam", "admin@pve"],
    "operators": ["root@pam"],
    "auditors": ["readonly@pam"],
}
