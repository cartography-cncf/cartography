from unittest.mock import patch

import requests

import cartography.intel.circleci.projects
import tests.data.circleci.projects
from tests.integration.cartography.intel.circleci.test_organizations import (
    _ensure_local_neo4j_has_test_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://circleci.fake/api/v2"
TEST_ORG_ID = "org-1111-aaaa"
TEST_SLUGS = ["gh/acme/web", "gh/acme/api"]


def _fake_get(api_session, base_url, slug):
    return tests.data.circleci.projects.CIRCLECI_PROJECTS[slug]


def _ensure_local_neo4j_has_test_projects(neo4j_session):
    projects = [
        cartography.intel.circleci.projects.transform(
            tests.data.circleci.projects.CIRCLECI_PROJECTS[slug],
        )
        for slug in TEST_SLUGS
    ]
    cartography.intel.circleci.projects.load_projects(
        neo4j_session,
        projects,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(cartography.intel.circleci.projects, "get", side_effect=_fake_get)
def test_load_circleci_projects(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
    }
    _ensure_local_neo4j_has_test_orgs(neo4j_session)

    # Act
    cartography.intel.circleci.projects.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_SLUGS,
    )

    # Assert projects exist
    assert check_nodes(neo4j_session, "CircleCIProject", ["id", "slug"]) == {
        ("proj-1", "gh/acme/web"),
        ("proj-2", "gh/acme/api"),
    }

    # Assert (Org)-[:RESOURCE]->(Project)
    assert check_rels(
        neo4j_session,
        "CircleCIProject",
        "id",
        "CircleCIOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("proj-1", TEST_ORG_ID),
        ("proj-2", TEST_ORG_ID),
    }
