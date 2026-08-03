from unittest.mock import patch

import requests

import cartography.intel.anthropic.ratelimits
import tests.data.anthropic.ratelimits
from tests.integration.cartography.intel.anthropic.test_organization import (
    _ensure_local_neo4j_has_test_organization,
)
from tests.integration.cartography.intel.anthropic.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "8834c225-ea27-405a-aea9-5ed5f07f4858"
TEST_WORKSPACE_ID = "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ"


@patch.object(
    cartography.intel.anthropic.ratelimits,
    "get_workspace_rate_limits",
    side_effect=lambda _session, _url, workspace_id: (
        tests.data.anthropic.ratelimits.ANTHROPIC_WORKSPACE_RATE_LIMITS[workspace_id]
    ),
)
@patch.object(
    cartography.intel.anthropic.ratelimits,
    "get",
    return_value=tests.data.anthropic.ratelimits.ANTHROPIC_RATE_LIMITS,
)
def test_load_anthropic_rate_limits(mock_api, mock_api_workspace, neo4j_session):
    """
    Ensure org and workspace rate limits get exploded into one node per limit
    """
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.anthropic.com/v1",
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_organization(neo4j_session)
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)

    # Act
    cartography.intel.anthropic.ratelimits.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        [TEST_WORKSPACE_ID],
    )

    # Assert each entry in a group's limits list became its own node, with an id
    # synthesised from scope, group type, models and limit type
    assert check_nodes(
        neo4j_session,
        "AnthropicRateLimit",
        ["id", "group_type", "limit_type", "value", "org_limit"],
    ) == {
        (
            "organization/model_group/claude-opus-5/requests_per_minute",
            "model_group",
            "requests_per_minute",
            4000,
            None,
        ),
        (
            "organization/model_group/claude-opus-5/input_tokens_per_minute",
            "model_group",
            "input_tokens_per_minute",
            400000,
            None,
        ),
        (
            "organization/web_search/all/requests_per_minute",
            "web_search",
            "requests_per_minute",
            1000,
            None,
        ),
        # The workspace override records the org value it displaces
        (
            f"{TEST_WORKSPACE_ID}/model_group/claude-opus-5/requests_per_minute",
            "model_group",
            "requests_per_minute",
            500,
            4000,
        ),
    }

    # Assert only the workspace-scoped limit edges to a workspace
    assert check_rels(
        neo4j_session,
        "AnthropicRateLimit",
        "id",
        "AnthropicWorkspace",
        "id",
        "CONTAINS",
        rel_direction_right=False,
    ) == {
        (
            f"{TEST_WORKSPACE_ID}/model_group/claude-opus-5/requests_per_minute",
            TEST_WORKSPACE_ID,
        ),
    }

    # Assert every limit is scoped to the org
    assert {
        org_id
        for _, org_id in check_rels(
            neo4j_session,
            "AnthropicRateLimit",
            "id",
            "AnthropicOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
    } == {TEST_ORG_ID}
