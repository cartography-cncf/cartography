"""
Mock data for Proxmox cluster tests.
"""

MOCK_CLUSTER_DATA = [
    {
        "type": "cluster",
        "name": "test-cluster",
        "version": "8.1.3",
        "quorate": 1,
        "nodes": 3,
        "id": "cluster/test-cluster",
    },
    {
        "type": "node",
        "name": "node1",
        "online": 1,
        "id": "node/node1",
    },
    {
        "type": "node",
        "name": "node2",
        "online": 1,
        "id": "node/node2",
    },
]

MOCK_NODE_DATA = [
    {
        "node": "node1",
        "status": "online",
        "uptime": 1234567,
        "cpu": 0.25,
        "maxcpu": 8,
        "mem": 8589934592,
        "maxmem": 33554432000,
        "disk": 107374182400,
        "maxdisk": 536870912000,
        "level": "",
        "id": "node/node1",
        "type": "node",
        "ip": "192.168.1.10",
    },
    {
        "node": "node2",
        "status": "online",
        "uptime": 987654,
        "cpu": 0.45,
        "maxcpu": 16,
        "mem": 17179869184,
        "maxmem": 67108864000,
        "disk": 214748364800,
        "maxdisk": 1073741824000,
        "level": "",
        "id": "node/node2",
        "type": "node",
        "ip": "192.168.1.11",
    },
]

MOCK_NODE_NETWORK_DATA = {
    "node1": [
        {
            "active": 1,
            "address": "192.168.1.10",
            "autostart": 1,
            "bridge_ports": "enp0s31f6",
            "cidr": "192.168.1.10/24",
            "gateway": "192.168.1.1",
            "iface": "vmbr0",
            "method": "static",
            "netmask": "255.255.255.0",
            "type": "bridge",
            "families": ["inet"],
        },
        {
            "active": 1,
            "address": "2001:db8::10",
            "address6": "2001:db8::10",
            "autostart": 1,
            "cidr6": "2001:db8::10/64",
            "gateway6": "2001:db8::1",
            "iface": "vmbr0",
            "method6": "static",
            "netmask6": 64,
            "type": "bridge",
            "families": ["inet", "inet6"],
        },
        {
            "active": 1,
            "autostart": 1,
            "iface": "enp0s31f6",
            "method": "manual",
            "type": "eth",
            "families": ["inet"],
        },
    ],
    "node2": [
        {
            "active": 1,
            "address": "192.168.1.11",
            "autostart": 1,
            "bridge_ports": "enp1s0 enp2s0",
            "cidr": "192.168.1.11/24",
            "gateway": "192.168.1.1",
            "iface": "vmbr0",
            "method": "static",
            "netmask": "255.255.255.0",
            "type": "bridge",
            "families": ["inet"],
        },
    ],
}
