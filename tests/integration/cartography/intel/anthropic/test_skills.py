import copy
from unittest.mock import patch

import requests

import cartography.intel.anthropic.skills
import tests.data.anthropic.skills
from tests.integration.cartography.intel.anthropic.test_organization import (
    _ensure_local_neo4j_has_test_organization,
)
from tests.integration.cartography.intel.anthropic.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_WORKSPACE_ID = "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ"


def _ensure_local_neo4j_has_test_skills(neo4j_session):
    cartography.intel.anthropic.skills.load_skills(
        neo4j_session,
        copy.deepcopy(tests.data.anthropic.skills.ANTHROPIC_SKILLS),
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.anthropic.skills,
    "get_skill_versions",
    side_effect=lambda _session, _url, skill_id: (
        tests.data.anthropic.skills.ANTHROPIC_SKILL_VERSIONS[skill_id]
    ),
)
@patch.object(
    cartography.intel.anthropic.skills,
    "get",
    return_value=copy.deepcopy(tests.data.anthropic.skills.ANTHROPIC_SKILLS),
)
def test_load_anthropic_skills(mock_api, mock_api_versions, neo4j_session):
    """
    Ensure that skills and their versions get loaded, scoped to their workspace
    """
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.anthropic.com/v1",
        "WORKSPACE_ID": TEST_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_organization(neo4j_session)
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)

    # Act
    cartography.intel.anthropic.skills.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert skills exist. source distinguishes a skill uploaded to this workspace
    # from a first-party one available everywhere.
    assert check_nodes(
        neo4j_session, "AnthropicSkill", ["id", "display_title", "source"]
    ) == {
        ("skill_01Mv4Zq7Nr2Ks8Ld3Tp6Wx9B", "Reactor Runbook", "custom"),
        ("skill_02Hb5Yn8Pq3Jt7Mc4Rd1Vz6A", "pptx", "anthropic"),
    }

    # Assert versions exist
    assert check_nodes(
        neo4j_session, "AnthropicSkillVersion", ["id", "name", "version"]
    ) == {
        (
            "skillver_01Qt9Wr4Ym6Nb2Kd8Lp3Xc7F",
            "reactor-runbook",
            "1738240000000000",
        ),
    }

    # Assert skills are scoped to the workspace, not the organization: there is no
    # org-wide skill listing
    assert check_rels(
        neo4j_session,
        "AnthropicSkill",
        "id",
        "AnthropicWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("skill_01Mv4Zq7Nr2Ks8Ld3Tp6Wx9B", TEST_WORKSPACE_ID),
        ("skill_02Hb5Yn8Pq3Jt7Mc4Rd1Vz6A", TEST_WORKSPACE_ID),
    }

    # Assert the version hangs off its skill
    assert check_rels(
        neo4j_session,
        "AnthropicSkill",
        "id",
        "AnthropicSkillVersion",
        "id",
        "HAS_VERSION",
        rel_direction_right=True,
    ) == {
        (
            "skill_01Mv4Zq7Nr2Ks8Ld3Tp6Wx9B",
            "skillver_01Qt9Wr4Ym6Nb2Kd8Lp3Xc7F",
        ),
    }
