from unittest.mock import patch

import requests

import cartography.intel.openai
import cartography.intel.openai.adminapikeys
import cartography.intel.openai.apikeys
import cartography.intel.openai.projects
import cartography.intel.openai.serviceaccounts
import cartography.intel.openai.users
import tests.data.openai.apikeys
import tests.data.openai.projects
import tests.data.openai.serviceaccounts
import tests.data.openai.users
from cartography.config import Config
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


@patch.object(cartography.intel.openai.projects, "get", return_value=[])
def test_project_cleanup_removes_keys_and_service_accounts_of_removed_project(
    mock_api,
    neo4j_session,
):
    """
    Ensure a project the API no longer returns takes its API keys and service
    accounts with it. Their own cleanups are scoped to a project and never run
    again for a project that is gone.
    """
    # Arrange: a project with a service account and two keys from an earlier sync
    project_id = tests.data.openai.projects.OPENAI_PROJECTS[0]["id"]
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)
    cartography.intel.openai.serviceaccounts.load_serviceaccounts(
        neo4j_session,
        tests.data.openai.serviceaccounts.OPENAI_SERVICEACCOUNTS,
        project_id,
        TEST_UPDATE_TAG,
    )
    cartography.intel.openai.apikeys.load_apikeys(
        neo4j_session,
        cartography.intel.openai.apikeys.transform(
            tests.data.openai.apikeys.OPENAI_APIKEYS,
        ),
        project_id,
        TEST_UPDATE_TAG,
    )

    # Act: the next sync finds no projects in the organization
    cartography.intel.openai.projects.sync(
        neo4j_session,
        requests.Session(),
        {
            "UPDATE_TAG": TEST_UPDATE_TAG + 1,
            "BASE_URL": "https://api.openai.con/v1",
            "ORG_ID": TEST_ORG_ID,
        },
        ORG_ID=TEST_ORG_ID,
    )

    # Assert
    assert check_nodes(neo4j_session, "OpenAIProject", ["id"]) == set()
    assert check_nodes(neo4j_session, "OpenAIApiKey", ["id"]) == set()
    assert check_nodes(neo4j_session, "OpenAIServiceAccount", ["id"]) == set()


@patch.object(cartography.intel.openai.adminapikeys, "get", return_value=[])
@patch.object(
    cartography.intel.openai.apikeys,
    "get",
    return_value=tests.data.openai.apikeys.OPENAI_APIKEYS,
)
@patch.object(
    cartography.intel.openai.serviceaccounts,
    "get",
    return_value=tests.data.openai.serviceaccounts.OPENAI_SERVICEACCOUNTS,
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
@patch.object(
    cartography.intel.openai.users,
    "get",
    return_value=tests.data.openai.users.OPENAI_USERS,
)
def test_sync_sweeps_keys_and_service_accounts_orphaned_by_older_versions(
    mock_users,
    mock_projects,
    mock_project_users,
    mock_serviceaccounts,
    mock_apikeys,
    mock_adminapikeys,
    neo4j_session,
):
    """
    Ensure a sync removes the API keys and service accounts that older versions
    left without a project, and keeps the ones that belong to a live project.
    """
    # Arrange: a key and a service account whose project was removed by an
    # older version, which did not cascade the removal to them.
    neo4j_session.run(
        """
        MERGE (k:OpenAIApiKey:APIKey {id: 'key_orphan'})
        SET k.lastupdated = $old_update_tag
        MERGE (sa:OpenAIServiceAccount {id: 'user-orphan'})
        SET sa.lastupdated = $old_update_tag
        """,
        old_update_tag=TEST_UPDATE_TAG - 1,
    )

    # Act
    cartography.intel.openai.start_openai_ingestion(
        neo4j_session,
        Config(
            neo4j_uri="bolt://unused",
            update_tag=TEST_UPDATE_TAG,
            openai_apikey="test-key",
            openai_org_id=TEST_ORG_ID,
        ),
    )

    # Assert
    assert check_nodes(neo4j_session, "OpenAIApiKey", ["id"]) == {
        ("key_Eek1lae1au5Iepi2eeza",),
        ("key_iegheiWieG2jupheeYin",),
    }
    assert check_nodes(neo4j_session, "OpenAIServiceAccount", ["id"]) == {
        ("user-ohp0mahG0Aw5eevu6ain",),
    }
