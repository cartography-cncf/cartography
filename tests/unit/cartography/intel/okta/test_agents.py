from datetime import datetime
from datetime import timezone

from cartography.intel.okta.agents import _transform_okta_agent_pools
from tests.data.okta.agent_pools import AGENT_POOLS


def test_transform_okta_agent_pools() -> None:
    # Act
    pools, agents = _transform_okta_agent_pools(AGENT_POOLS)

    # Assert
    assert pools == [
        {
            "id": "pool-ldap",
            "name": "LDAP pool",
            "type": "LDAP",
            "operational_status": "DEGRADED",
            "disrupted_agents": 0,
            "inactive_agents": 1,
        },
        {
            "id": "pool-radius",
            "name": "RADIUS pool",
            "type": "Radius",
            "operational_status": "OPERATIONAL",
            "disrupted_agents": 0,
            "inactive_agents": 0,
        },
    ]
    assert agents == [
        {
            "id": "agent-ldap-old",
            "name": "ldap-01.example.com",
            "type": "LDAP",
            "version": "5.26.2",
            "is_latest_ga_version": False,
            "is_hidden": False,
            "operational_status": "INACTIVE",
            "last_connection": datetime(2025, 11, 20, tzinfo=timezone.utc),
            "update_status": "Scheduled",
            "update_message": "",
            "pool_id": "pool-ldap",
        },
        {
            "id": "agent-ldap-new",
            "name": "ldap-02.example.com",
            "type": "LDAP",
            "version": "5.26.3",
            "is_latest_ga_version": True,
            "is_hidden": False,
            "operational_status": "OPERATIONAL",
            "last_connection": datetime(2025, 11, 21, tzinfo=timezone.utc),
            "update_status": "Success",
            "update_message": "",
            "pool_id": "pool-ldap",
        },
    ]


def test_transform_okta_agent_pools_falls_back_to_pool_fields() -> None:
    # Arrange
    raw = [
        {
            "id": "pool-opp",
            "type": "OPP",
            "agents": [{"id": "agent-opp", "version": "3.3.3"}],
        },
    ]

    # Act
    _, agents = _transform_okta_agent_pools(raw)

    # Assert
    assert agents[0]["type"] == "OPP"
    assert agents[0]["pool_id"] == "pool-opp"
    assert agents[0]["last_connection"] is None
