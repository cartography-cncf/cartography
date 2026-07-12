from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.apikeys
import tests.data.gcp.apikeys
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project-123"


def _create_test_project(neo4j_session):
    neo4j_session.run(
        """
        MERGE (project:GCPProject{id: $project_id})
        ON CREATE SET project.firstseen = timestamp()
        SET project.lastupdated = $update_tag
        """,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.gcp.apikeys,
    "get_api_keys",
    return_value=tests.data.gcp.apikeys.LIST_API_KEYS_RESPONSE,
)
def test_sync_apikeys(mock_get_api_keys, neo4j_session):
    """Test that sync() loads API Keys and creates the RESOURCE relationship."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }

    cartography.intel.gcp.apikeys.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "GCPApiKey",
        ["id", "display_name", "restricted"],
    ) == {
        (
            "projects/test-project-123/locations/global/keys/key-abc",
            "Browser key (unrestricted)",
            False,
        ),
        (
            "projects/test-project-123/locations/global/keys/key-def",
            "Maps key (restricted)",
            True,
        ),
    }

    # Real API Keys must also carry the APIKey ontology label and the
    # normalized _ont_* fields (display_name falls back to the resource name).
    assert check_nodes(
        neo4j_session,
        "APIKey",
        ["id", "_ont_source", "_ont_name"],
    ) >= {
        (
            "projects/test-project-123/locations/global/keys/key-abc",
            "gcp",
            "Browser key (unrestricted)",
        ),
        (
            "projects/test-project-123/locations/global/keys/key-def",
            "gcp",
            "Maps key (restricted)",
        ),
    }

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPApiKey",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, "projects/test-project-123/locations/global/keys/key-abc"),
        (TEST_PROJECT_ID, "projects/test-project-123/locations/global/keys/key-def"),
    }
