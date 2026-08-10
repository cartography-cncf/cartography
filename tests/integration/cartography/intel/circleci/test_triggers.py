from unittest.mock import patch

import requests

import cartography.intel.circleci.triggers
import tests.data.circleci.pipelines
import tests.data.circleci.triggers
from tests.integration.cartography.intel.circleci.test_organizations import (
    _ensure_local_neo4j_has_test_orgs,
)
from tests.integration.cartography.intel.circleci.test_pipelines import (
    _ensure_local_neo4j_has_test_pipelines,
)
from tests.integration.cartography.intel.circleci.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://circleci.fake/api/v2"
TEST_PROJECT_ID = "proj-1"


def _fake_get(api_session, base_url, project_id, pipeline_id):
    return tests.data.circleci.triggers.CIRCLECI_TRIGGERS[pipeline_id]


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
    _ensure_local_neo4j_has_test_pipelines(neo4j_session)

    # Act
    cartography.intel.circleci.triggers.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        tests.data.circleci.pipelines.CIRCLECI_PIPELINES,
    )

    # Assert both triggers exist; the scheduled one carries its cron expression.
    assert check_nodes(
        neo4j_session,
        "CircleCITrigger",
        ["id", "event_source_provider", "cron_expression"],
    ) == {
        ("trig-1", "github_app", None),
        ("trig-2", "schedule", "0 19 6 * *"),
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
        ("trig-2", TEST_PROJECT_ID),
    }
    # (Pipeline)-[:HAS_TRIGGER]->(Trigger)
    assert check_rels(
        neo4j_session,
        "CircleCITrigger",
        "id",
        "CircleCIPipeline",
        "id",
        "HAS_TRIGGER",
        rel_direction_right=False,
    ) == {
        ("trig-1", "def-1"),
        ("trig-2", "def-1"),
    }
