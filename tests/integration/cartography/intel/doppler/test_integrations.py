from unittest.mock import patch

import requests

import cartography.intel.doppler.configs
import cartography.intel.doppler.integrations
import cartography.intel.doppler.projects
import cartography.intel.doppler.webhooks
import cartography.intel.doppler.workplace
import tests.data.doppler.doppler as data
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_WORKPLACE_ID = "wp1"


def _common():
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.doppler.com/v3",
        "WORKPLACE_ID": TEST_WORKPLACE_ID,
    }


@patch.object(cartography.intel.doppler.webhooks, "get", return_value=data.WEBHOOKS)
@patch.object(
    cartography.intel.doppler.integrations, "get", return_value=data.INTEGRATIONS
)
@patch.object(cartography.intel.doppler.configs, "get", return_value=data.CONFIGS)
@patch.object(cartography.intel.doppler.projects, "get", return_value=data.PROJECTS)
@patch.object(cartography.intel.doppler.workplace, "get", return_value=data.WORKPLACE)
def test_doppler_integrations_and_webhooks(
    mock_wp, mock_proj, mock_conf, mock_int, mock_wh, neo4j_session
):
    # Arrange
    api_session = requests.Session()
    common = _common()

    # Act: configs must exist so the secret sync SYNCS edge can resolve.
    cartography.intel.doppler.workplace.sync(neo4j_session, api_session, common)
    project_slugs = cartography.intel.doppler.projects.sync(
        neo4j_session, api_session, common
    )
    cartography.intel.doppler.configs.sync(
        neo4j_session, api_session, project_slugs, common
    )
    cartography.intel.doppler.integrations.sync(neo4j_session, api_session, common)
    cartography.intel.doppler.webhooks.sync(
        neo4j_session, api_session, project_slugs, common
    )

    # Assert: integration node + RESOURCE edge
    assert check_nodes(neo4j_session, "DopplerIntegration", ["id", "type"]) == {
        ("int1", "aws_secrets_manager")
    }

    # Assert: the camelCase lastSyncedAt is mapped onto the node
    assert check_nodes(
        neo4j_session, "DopplerSecretSync", ["id", "last_synced_at"]
    ) == {("sync1", "2024-02-03T00:00:00Z")}

    # Assert: secret sync USES integration and SYNCS config
    assert check_rels(
        neo4j_session,
        "DopplerSecretSync",
        "id",
        "DopplerIntegration",
        "id",
        "USES",
        rel_direction_right=True,
    ) == {("sync1", "int1")}
    assert check_rels(
        neo4j_session,
        "DopplerSecretSync",
        "id",
        "DopplerConfig",
        "id",
        "SYNCS",
        rel_direction_right=True,
    ) == {("sync1", "backend/dev")}

    # Assert: webhook has no secret property and is linked to its project
    assert check_nodes(neo4j_session, "DopplerWebhook", ["id", "url"]) == {
        ("wh1", "https://hooks.slack.com/services/xxx")
    }
    assert check_rels(
        neo4j_session,
        "DopplerProject",
        "slug",
        "DopplerWebhook",
        "id",
        "HAS_WEBHOOK",
        rel_direction_right=True,
    ) == {("backend", "wh1")}
