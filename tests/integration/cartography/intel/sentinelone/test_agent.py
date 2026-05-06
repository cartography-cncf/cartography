import cartography.intel.sentinelone.agent
from tests.data.sentinelone.agent import AGENT_ID
from tests.data.sentinelone.agent import AGENT_ID_2
from tests.data.sentinelone.agent import AGENT_ID_3
from tests.data.sentinelone.agent import AGENTS_DATA
from tests.data.sentinelone.agent import TEST_ACCOUNT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_API_URL = "https://test-api.sentinelone.net"
TEST_API_TOKEN = "test-api-token"


def test_sync_agents(neo4j_session, mocker):
    """
    Test that agent sync works properly by syncing agents and verifying nodes and relationships
    """
    # Mock the API call to return test data
    mocker.patch(
        "cartography.intel.sentinelone.agent.get_paginated_results",
        return_value=AGENTS_DATA,
    )

    # Create common job parameters
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "API_URL": TEST_API_URL,
        "API_TOKEN": TEST_API_TOKEN,
        "S1_ACCOUNT_ID": TEST_ACCOUNT_ID,
    }

    # First, we need to create the account node for the relationship
    neo4j_session.run(
        "CREATE (a:S1Account {id: $account_id, lastupdated: $update_tag})",
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Run the sync
    cartography.intel.sentinelone.agent.sync(
        neo4j_session,
        common_job_parameters,
    )

    # Verify that the correct agent nodes were created
    expected_nodes = {
        (
            AGENT_ID,
            "uuid-123-456-789",
            "test-computer-01",
            True,
            "Windows 10",
            "1909",
            "test.local",
            "2023-12-01T10:00:00Z",
            "2023-12-01T09:00:00Z",
            "finished",
            "SN123456",
        ),
        (
            AGENT_ID_2,
            "uuid-456-789-123",
            "test-computer-02",
            False,
            "Ubuntu 20.04",
            "5.4.0-89-generic",
            "test.local",
            "2023-12-01T11:00:00Z",
            "2023-12-01T10:30:00Z",
            "finished",
            "SN789012",
        ),
        (
            AGENT_ID_3,
            "uuid-789-123-456",
            "test-computer-03",
            True,
            "macOS",
            "12.6.1",
            None,  # No domain for macOS
            "2023-12-01T12:00:00Z",
            None,  # Never completed scan
            "in_progress",
            "SN345678",
        ),
    }

    actual_nodes = check_nodes(
        neo4j_session,
        "S1Agent",
        [
            "id",
            "uuid",
            "computer_name",
            "firewall_enabled",
            "os_name",
            "os_revision",
            "domain",
            "last_active",
            "last_successful_scan",
            "scan_status",
            "serial_number",
        ],
    )

    assert actual_nodes == expected_nodes

    # Verify that relationships to the account were created
    expected_rels = {
        (AGENT_ID, TEST_ACCOUNT_ID),
        (AGENT_ID_2, TEST_ACCOUNT_ID),
        (AGENT_ID_3, TEST_ACCOUNT_ID),
    }

    actual_rels = check_rels(
        neo4j_session,
        "S1Agent",
        "id",
        "S1Account",
        "id",
        "RESOURCE",
        rel_direction_right=False,  # (:S1Agent)<-[:RESOURCE]-(:S1Account)
    )

    assert actual_rels == expected_rels

    # Verify that the lastupdated field was set correctly
    result = neo4j_session.run(
        "MATCH (a:S1Agent) RETURN a.lastupdated as lastupdated LIMIT 1"
    )
    record = result.single()
    assert record["lastupdated"] == TEST_UPDATE_TAG


def test_sync_agents_empty_response(neo4j_session, mocker):
    """
    Test that agent sync handles empty API response correctly
    """
    # Clean up any existing agent data from previous tests
    neo4j_session.run("MATCH (a:S1Agent) DETACH DELETE a")

    # Mock the API call to return empty data
    mocker.patch(
        "cartography.intel.sentinelone.agent.get_paginated_results",
        return_value=[],
    )

    # Create common job parameters
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "API_URL": TEST_API_URL,
        "API_TOKEN": TEST_API_TOKEN,
        "S1_ACCOUNT_ID": TEST_ACCOUNT_ID,
    }

    # Run the sync
    cartography.intel.sentinelone.agent.sync(
        neo4j_session,
        common_job_parameters,
    )

    # Verify that no agent nodes were created
    actual_nodes = check_nodes(neo4j_session, "S1Agent", ["id"])
    assert actual_nodes == set()


def test_sync_agents_cleanup(neo4j_session, mocker):
    """
    Test that agent sync properly cleans up stale agents
    """
    # Create an old agent that should be cleaned up
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (old:S1Agent {
            id: 'old-agent-123',
            computer_name: 'old-computer',
            lastupdated: $old_update_tag
        })
        CREATE (acc:S1Account {id: $account_id, lastupdated: $update_tag})
        CREATE (old)<-[:RESOURCE]-(acc)
        """,
        old_update_tag=old_update_tag,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Mock the API call to return only new agents
    mocker.patch(
        "cartography.intel.sentinelone.agent.get_paginated_results",
        return_value=[AGENTS_DATA[0]],  # Only first agent
    )

    # Create common job parameters
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "API_URL": TEST_API_URL,
        "API_TOKEN": TEST_API_TOKEN,
        "S1_ACCOUNT_ID": TEST_ACCOUNT_ID,
    }

    # Run the sync
    cartography.intel.sentinelone.agent.sync(
        neo4j_session,
        common_job_parameters,
    )

    # Verify that only the new agent exists
    result = neo4j_session.run("MATCH (a:S1Agent) RETURN a.id as id")
    existing_agents = {record["id"] for record in result}

    assert "old-agent-123" not in existing_agents
    assert AGENT_ID in existing_agents
