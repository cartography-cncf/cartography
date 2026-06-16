from unittest.mock import patch

import requests

import cartography.intel.circleci.triggers
import tests.data.circleci.pipeline_definitions
import tests.data.circleci.triggers
from tests.integration.cartography.intel.circleci.test_organizations import (
    _ensure_local_neo4j_has_test_orgs,
)
from tests.integration.cartography.intel.circleci.test_pipeline_definitions import (
    _ensure_local_neo4j_has_test_definitions,
)
from tests.integration.cartography.intel.circleci.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://circleci.fake/api/v2"
TEST_PROJECT_ID = "proj-1"


def _fake_get(api_session, base_url, project_id, definition_id):
    return tests.data.circleci.triggers.CIRCLECI_TRIGGERS[definition_id]


@patch.object(cartography.intel.circleci.triggers, "get", side_effect=_fake_get)
def test_load_circleci_triggers(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _ensure_local_neo4j_has_test_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)
    _ensure_local_neo4j_has_test_definitions(neo4j_session)

    # Act
    cartography.intel.circleci.triggers.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        tests.data.circleci.pipeline_definitions.CIRCLECI_PIPELINE_DEFINITIONS,
    )

    # Assert
    assert check_nodes(neo4j_session, "CircleCITrigger", ["id", "event_name"]) == {
        ("trig-1", "push"),
    }
    # (Project)-[:RESOURCE]->(Trigger)
    assert check_rels(
        neo4j_session,
        "CircleCITrigger",
        "id",
        "CircleCIProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("trig-1", TEST_PROJECT_ID),
    }
    # (PipelineDefinition)-[:HAS_TRIGGER]->(Trigger)
    assert check_rels(
        neo4j_session,
        "CircleCITrigger",
        "id",
        "CircleCIPipelineDefinition",
        "id",
        "HAS_TRIGGER",
        rel_direction_right=False,
    ) == {
        ("trig-1", "def-1"),
    }
