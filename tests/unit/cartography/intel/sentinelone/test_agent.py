import pytest

from cartography.intel.sentinelone.agent import transform_agents
from tests.data.sentinelone.agent import AGENT_ID
from tests.data.sentinelone.agent import AGENT_ID_2
from tests.data.sentinelone.agent import AGENT_ID_3
from tests.data.sentinelone.agent import AGENTS_DATA
from tests.data.sentinelone.agent import AGENTS_DATA_MINIMAL


def test_transform_agents():
    """
    Test that transform_agents correctly transforms raw API data with field mapping and data types
    """
    result = transform_agents(AGENTS_DATA)

    assert len(result) == 3

    # Test first agent (Windows with all fields)
    agent1 = result[0]
    assert agent1["id"] == AGENT_ID
    assert agent1["uuid"] == "uuid-123-456-789"
    assert agent1["computer_name"] == "test-computer-01"
    assert agent1["firewall_enabled"] is True
    assert agent1["os_name"] == "Windows 10"
    assert agent1["os_revision"] == "1909"
    assert agent1["domain"] == "test.local"
    assert agent1["last_active"] == "2023-12-01T10:00:00Z"
    assert agent1["last_successful_scan"] == "2023-12-01T09:00:00Z"
    assert agent1["scan_status"] == "finished"
    assert agent1["serial_number"] == "SN123456"

    # Test second agent (Linux with different values)
    agent2 = result[1]
    assert agent2["id"] == AGENT_ID_2
    assert agent2["firewall_enabled"] is False  # Boolean type preservation
    assert agent2["os_name"] == "Ubuntu 20.04"

    # Test third agent (macOS with None fields)
    agent3 = result[2]
    assert agent3["id"] == AGENT_ID_3
    assert agent3["domain"] is None  # None value handling
    assert agent3["last_successful_scan"] is None  # None value handling


def test_transform_agents_missing_optional_fields():
    """
    Test that transform_agents handles missing optional fields gracefully
    """
    result = transform_agents(AGENTS_DATA_MINIMAL)

    assert len(result) == 1
    agent = result[0]

    # Required field should be present
    assert agent["id"] == "minimal-agent-001"

    # Optional fields should be None
    assert agent["uuid"] is None
    assert agent["computer_name"] is None
    assert agent["firewall_enabled"] is None
    assert agent["os_name"] is None
    assert agent["os_revision"] is None
    assert agent["domain"] is None
    assert agent["last_active"] is None
    assert agent["last_successful_scan"] is None
    assert agent["scan_status"] is None
    assert agent["serial_number"] is None


def test_transform_agents_missing_required_field():
    """
    Test that transform_agents raises KeyError when required field is missing
    """
    test_data = [
        {
            "uuid": "uuid-123",
            "computerName": "test-computer",
            # Missing required 'id' field
        }
    ]

    with pytest.raises(KeyError):
        transform_agents(test_data)


def test_transform_agents_empty_list():
    """
    Test that transform_agents handles empty input list
    """
    result = transform_agents([])
    assert result == []
