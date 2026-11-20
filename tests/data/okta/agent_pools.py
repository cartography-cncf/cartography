from typing import Any

# Synthetic raw API payloads for GET /api/v1/agentPools.

AGENT_POOLS: list[dict[str, Any]] = [
    {
        "id": "pool-ldap",
        "name": "LDAP pool",
        "type": "LDAP",
        "operationalStatus": "DEGRADED",
        "disruptedAgents": 0,
        "inactiveAgents": 1,
        "agents": [
            {
                "id": "agent-ldap-old",
                "name": "ldap-01.example.com",
                "type": "LDAP",
                "version": "5.26.2",
                "isLatestGAedVersion": False,
                "isHidden": False,
                "operationalStatus": "INACTIVE",
                "lastConnection": 1763596800000,
                "updateStatus": "Scheduled",
                "updateMessage": "",
                "poolId": "pool-ldap",
                "_links": {},
            },
            {
                "id": "agent-ldap-new",
                "name": "ldap-02.example.com",
                "type": "LDAP",
                "version": "5.26.3",
                "isLatestGAedVersion": True,
                "isHidden": False,
                "operationalStatus": "OPERATIONAL",
                "lastConnection": 1763683200000,
                "updateStatus": "Success",
                "updateMessage": "",
                "poolId": "pool-ldap",
                "_links": {},
            },
        ],
        "_links": {},
    },
    {
        "id": "pool-radius",
        "name": "RADIUS pool",
        "type": "Radius",
        "operationalStatus": "OPERATIONAL",
        "disruptedAgents": 0,
        "inactiveAgents": 0,
        "agents": [],
        "_links": {},
    },
]
