from unittest.mock import patch

import cartography.intel.endorlabs.projects
import tests.data.endorlabs.projects
from cartography.client.core.tx import load
from cartography.models.endorlabs.namespace import EndorLabsNamespaceSchema
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_NAMESPACE = "acme-corp"


def _load_namespace(neo4j_session):
    load(
        neo4j_session,
        EndorLabsNamespaceSchema(),
        [{"id": TEST_NAMESPACE, "name": TEST_NAMESPACE}],
        lastupdated=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.endorlabs.projects,
    "get",
    return_value=tests.data.endorlabs.projects.PROJECTS_RESPONSE["list"]["objects"],
)
def test_sync_projects(mock_api, neo4j_session):
    _load_namespace(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "NAMESPACE_ID": TEST_NAMESPACE,
    }

    cartography.intel.endorlabs.projects.sync_projects(
        neo4j_session,
        "fake-token",
        TEST_NAMESPACE,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    expected_nodes = {
        ("proj-001", "acme/frontend-app", "PLATFORM_SOURCE_GITHUB"),
        ("proj-002", "acme/backend-api", "PLATFORM_SOURCE_GITHUB"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "EndorLabsProject",
            ["id", "name", "platform_source"],
        )
        == expected_nodes
    )

    # Assert: Connected to namespace
    expected_ns_rels = {
        ("proj-001", TEST_NAMESPACE),
        ("proj-002", TEST_NAMESPACE),
    }
    assert (
        check_rels(
            neo4j_session,
            "EndorLabsProject",
            "id",
            "EndorLabsNamespace",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_ns_rels
    )
