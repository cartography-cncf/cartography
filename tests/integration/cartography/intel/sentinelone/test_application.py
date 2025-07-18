from unittest.mock import patch

import cartography.intel.sentinelone.application
from tests.data.sentinelone.application import AGENT_UUID_1
from tests.data.sentinelone.application import AGENT_UUID_2
from tests.data.sentinelone.application import AGENT_UUID_3
from tests.data.sentinelone.application import APP_VERSION_ID_1
from tests.data.sentinelone.application import APP_VERSION_ID_2
from tests.data.sentinelone.application import APP_VERSION_ID_3
from tests.data.sentinelone.application import APP_VERSION_ID_4
from tests.data.sentinelone.application import APPLICATION_ID_1
from tests.data.sentinelone.application import APPLICATION_ID_2
from tests.data.sentinelone.application import APPLICATION_ID_3
from tests.data.sentinelone.application import APPLICATION_INSTALLS_DATA
from tests.data.sentinelone.application import APPLICATIONS_DATA
from tests.data.sentinelone.application import TEST_ACCOUNT_ID
from tests.data.sentinelone.application import TEST_COMMON_JOB_PARAMETERS
from tests.data.sentinelone.application import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


@patch.object(
    cartography.intel.sentinelone.application,
    "get_paginated_results",
)
def test_sync_applications(mock_get_paginated_results, neo4j_session):
    """
    Test that application sync works properly by syncing applications and verifying nodes and relationships
    """
    # Mock the API calls to return test data
    # First call is for applications, second and subsequent calls are for installs per application
    mock_get_paginated_results.side_effect = [
        APPLICATIONS_DATA,  # get_application_data call
        [
            APPLICATION_INSTALLS_DATA[0],
            APPLICATION_INSTALLS_DATA[1],
        ],  # Office 365 installs
        [APPLICATION_INSTALLS_DATA[2]],  # Chrome installs
        [APPLICATION_INSTALLS_DATA[3]],  # Photoshop installs
    ]

    # Create prerequisite nodes: account and agents
    neo4j_session.run(
        "CREATE (a:S1Account {id: $account_id, lastupdated: $update_tag})",
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    neo4j_session.run(
        """
        CREATE (agent1:S1Agent {id: 'agent-1', uuid: $uuid1, lastupdated: $update_tag})
        CREATE (agent2:S1Agent {id: 'agent-2', uuid: $uuid2, lastupdated: $update_tag})
        CREATE (agent3:S1Agent {id: 'agent-3', uuid: $uuid3, lastupdated: $update_tag})
        """,
        uuid1=AGENT_UUID_1,
        uuid2=AGENT_UUID_2,
        uuid3=AGENT_UUID_3,
        update_tag=TEST_UPDATE_TAG,
    )

    # Run the sync
    cartography.intel.sentinelone.application.sync(
        neo4j_session,
        TEST_COMMON_JOB_PARAMETERS,
    )

    # Verify that the correct application nodes were created
    expected_application_nodes = {
        (APPLICATION_ID_1, "Office 365", "Microsoft"),
        (APPLICATION_ID_2, "Chrome", "Google"),
        (APPLICATION_ID_3, "Photoshop", "Adobe"),
    }

    actual_application_nodes = check_nodes(
        neo4j_session,
        "S1Application",
        ["id", "name", "vendor"],
    )

    assert actual_application_nodes == expected_application_nodes

    # Verify that application relationships to account were created
    expected_app_account_rels = {
        (APPLICATION_ID_1, TEST_ACCOUNT_ID),
        (APPLICATION_ID_2, TEST_ACCOUNT_ID),
        (APPLICATION_ID_3, TEST_ACCOUNT_ID),
    }

    actual_app_account_rels = check_rels(
        neo4j_session,
        "S1Application",
        "id",
        "S1Account",
        "id",
        "RESOURCE",
        rel_direction_right=False,  # (:S1Application)<-[:RESOURCE]-(:S1Account)
    )

    assert actual_app_account_rels == expected_app_account_rels

    # Verify that the correct application version nodes were created
    expected_version_nodes = {
        (
            APP_VERSION_ID_1,
            "Office 365",
            "Microsoft",
            "2021.16.54",
        ),
        (
            APP_VERSION_ID_2,
            "Office 365",
            "Microsoft",
            "2021.16.52",
        ),
        (
            APP_VERSION_ID_3,
            "Chrome",
            "Google",
            "119.0.6045.105",
        ),
        (
            APP_VERSION_ID_4,
            "Photoshop",
            "Adobe",
            "2023.24.1",
        ),
    }

    actual_version_nodes = check_nodes(
        neo4j_session,
        "S1ApplicationVersion",
        ["id", "application_name", "application_vendor", "version"],
    )

    assert actual_version_nodes == expected_version_nodes

    # Verify that application version relationships to account were created
    expected_version_account_rels = {
        (APP_VERSION_ID_1, TEST_ACCOUNT_ID),
        (APP_VERSION_ID_2, TEST_ACCOUNT_ID),
        (APP_VERSION_ID_3, TEST_ACCOUNT_ID),
        (APP_VERSION_ID_4, TEST_ACCOUNT_ID),
    }

    actual_version_account_rels = check_rels(
        neo4j_session,
        "S1ApplicationVersion",
        "id",
        "S1Account",
        "id",
        "RESOURCE",
        rel_direction_right=False,  # (:S1ApplicationVersion)<-[:RESOURCE]-(:S1Account)
    )

    assert actual_version_account_rels == expected_version_account_rels

    # Verify that application version relationships to applications were created
    expected_version_app_rels = {
        (APP_VERSION_ID_1, APPLICATION_ID_1),
        (APP_VERSION_ID_2, APPLICATION_ID_1),
        (APP_VERSION_ID_3, APPLICATION_ID_2),
        (APP_VERSION_ID_4, APPLICATION_ID_3),
    }

    actual_version_app_rels = check_rels(
        neo4j_session,
        "S1ApplicationVersion",
        "id",
        "S1Application",
        "id",
        "VERSION",
        rel_direction_right=False,  # (:S1ApplicationVersion)<-[:VERSION]-(:S1Application)
    )

    assert actual_version_app_rels == expected_version_app_rels

    # Verify that application version relationships to agents were created
    expected_version_agent_rels = {
        (AGENT_UUID_1, APP_VERSION_ID_1),
        (AGENT_UUID_2, APP_VERSION_ID_2),
        (AGENT_UUID_1, APP_VERSION_ID_3),
        (AGENT_UUID_3, APP_VERSION_ID_4),
    }

    actual_version_agent_rels = check_rels(
        neo4j_session,
        "S1Agent",
        "uuid",
        "S1ApplicationVersion",
        "id",
        "HAS_INSTALLED",
        rel_direction_right=True,  # (:S1Agent)-[:HAS_INSTALLED]->(:S1ApplicationVersion)
    )

    assert actual_version_agent_rels == expected_version_agent_rels


@patch.object(
    cartography.intel.sentinelone.application,
    "get_paginated_results",
)
def test_sync_applications_cleanup(mock_get_paginated_results, neo4j_session):
    """
    Test that application sync properly cleans up stale data
    """
    # First sync: Create applications with update tag 1
    mock_get_paginated_results.side_effect = [
        APPLICATIONS_DATA[:2],  # Only first 2 applications
        [APPLICATION_INSTALLS_DATA[0]],  # Office 365 installs
        [APPLICATION_INSTALLS_DATA[2]],  # Chrome installs
    ]

    # Create prerequisite nodes
    neo4j_session.run(
        "CREATE (a:S1Account {id: $account_id, lastupdated: 1})",
        account_id=TEST_ACCOUNT_ID,
    )

    # Create agents
    neo4j_session.run(
        """
        CREATE (agent1:S1Agent {id: 'agent-1', uuid: $uuid1, lastupdated: 1})
        CREATE (agent2:S1Agent {id: 'agent-2', uuid: $uuid2, lastupdated: 1})
        """,
        uuid1=AGENT_UUID_1,
        uuid2=AGENT_UUID_2,
    )

    first_sync_parameters = {
        "UPDATE_TAG": 1,
        "API_URL": "https://test-api.sentinelone.net",
        "API_TOKEN": "test-api-token",
        "S1_ACCOUNT_ID": TEST_ACCOUNT_ID,
    }

    cartography.intel.sentinelone.application.sync(
        neo4j_session,
        first_sync_parameters,
    )

    # Verify first sync created 2 applications
    actual_nodes_after_first = check_nodes(
        neo4j_session,
        "S1Application",
        ["id"],
    )
    assert len(actual_nodes_after_first) == 2

    # Second sync: Create different applications with update tag 2
    mock_get_paginated_results.side_effect = [
        [APPLICATIONS_DATA[2]],  # Only Photoshop
        [APPLICATION_INSTALLS_DATA[3]],  # Photoshop installs
    ]

    # Create agent for Photoshop
    neo4j_session.run(
        "CREATE (agent3:S1Agent {id: 'agent-3', uuid: $uuid3, lastupdated: 2})",
        uuid3=AGENT_UUID_3,
    )

    second_sync_parameters = {
        "UPDATE_TAG": 2,
        "API_URL": "https://test-api.sentinelone.net",
        "API_TOKEN": "test-api-token",
        "S1_ACCOUNT_ID": TEST_ACCOUNT_ID,
    }

    cartography.intel.sentinelone.application.sync(
        neo4j_session,
        second_sync_parameters,
    )

    # Verify cleanup removed old applications and only new one exists
    actual_nodes_after_second = check_nodes(
        neo4j_session,
        "S1Application",
        ["id"],
    )
    assert actual_nodes_after_second == {(APPLICATION_ID_3,)}

    # Verify old application versions were also cleaned up
    actual_versions_after_second = check_nodes(
        neo4j_session,
        "S1ApplicationVersion",
        ["id"],
    )
    assert actual_versions_after_second == {(APP_VERSION_ID_4,)}
