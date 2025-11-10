"""
Mock data for Proxmox HA tests.
"""

MOCK_HA_GROUP_DATA = [
    {
        "group": "ha-group-1",
        "nodes": "node1,node2",
        "restricted": 0,
        "nofailback": 0,
        "comment": "Primary HA group",
    },
    {
        "group": "ha-group-2",
        "nodes": "node2",
        "restricted": 1,
        "nofailback": 1,
        "comment": "Secondary HA group with restrictions",
    },
]

MOCK_HA_RESOURCE_DATA = [
    {
        "sid": "vm:100",
        "state": "started",
        "group": "ha-group-1",
        "max_restart": 3,
        "max_relocate": 2,
        "comment": "Production VM with HA",
    },
    {
        "sid": "ct:200",
        "state": "started",
        "group": "ha-group-1",
        "max_restart": 2,
        "max_relocate": 1,
        "comment": "Production container with HA",
    },
    {
        "sid": "vm:101",
        "state": "stopped",
        "group": "ha-group-2",
        "max_restart": 1,
        "max_relocate": 0,
    },
]
