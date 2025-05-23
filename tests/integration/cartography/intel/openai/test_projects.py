from unittest.mock import patch

import requests

import cartography.intel.openai.projects
import tests.data.openai.projects
from tests.integration.cartography.intel.openai.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "org-iwai3meew4phaeNgu8ae"


def _ensure_local_neo4j_has_test_projects(neo4j_session):
    cartography.intel.openai.projects.load_projects(
        neo4j_session,
        tests.data.openai.projects.OPENAI_PROJECTS,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.openai.projects,
    "get_project_users",
    return_value=tests.data.openai.projects.OPENAI_PROJECTS_MEMBERS,
)
@patch.object(
    cartography.intel.openai.projects,
    "get",
    return_value=tests.data.openai.projects.OPENAI_PROJECTS,
)
def test_load_openai_projects(mock_api, mock_api_members, neo4j_session):
    """
    Ensure that projects actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.openai.con/v1",
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Act
    cartography.intel.openai.projects.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        ORG_ID=TEST_ORG_ID,
    )

    # Assert Projects exist
    expected_nodes = {
        (
            "proj_Eicie2Iid8ii4aiNg8va",
            "Springfield Nuclear Power Plant",
        ),
    }
    assert check_nodes(neo4j_session, "OpenAIProject", ["id", "name"]) == expected_nodes

    # Assert projects are linked to the correct org
    expected_rels = {
        ("proj_Eicie2Iid8ii4aiNg8va", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "OpenAIProject",
            "id",
            "OpenAIOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert projects are linked to the correct users
    expected_rels = {
        ("user-ou3doohoeX6xie1Quiem", "proj_Eicie2Iid8ii4aiNg8va"),
        ("user-uJeighaeFair8shaa2av", "proj_Eicie2Iid8ii4aiNg8va"),
    }
    assert (
        check_rels(
            neo4j_session,
            "OpenAIUser",
            "id",
            "OpenAIProject",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
    expected_rels = {("user-ou3doohoeX6xie1Quiem", "proj_Eicie2Iid8ii4aiNg8va")}
    assert (
        check_rels(
            neo4j_session,
            "OpenAIUser",
            "id",
            "OpenAIProject",
            "id",
            "ADMIN_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
