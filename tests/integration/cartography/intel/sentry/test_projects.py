from unittest.mock import patch

import requests

import cartography.intel.sentry.organizations
import cartography.intel.sentry.projects
import cartography.intel.sentry.teams
import tests.data.sentry.organizations
import tests.data.sentry.projects
import tests.data.sentry.teams
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "100"
TEST_ORG_SLUG = "simpson-corp"
TEST_BASE_URL = "https://sentry.io/api/0"


def _setup_org_and_teams(neo4j_session):
    """Create prerequisite org and team nodes."""
    with patch.object(
        cartography.intel.sentry.organizations,
        "get",
        return_value=tests.data.sentry.organizations.SENTRY_ORGANIZATIONS,
    ):
        cartography.intel.sentry.organizations.sync(
            neo4j_session,
            requests.Session(),
            TEST_UPDATE_TAG,
            TEST_BASE_URL,
        )

    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}
    with patch.object(
        cartography.intel.sentry.teams,
        "get",
        return_value=tests.data.sentry.teams.SENTRY_TEAMS,
    ):
        cartography.intel.sentry.teams.sync(
            neo4j_session,
            requests.Session(),
            TEST_ORG_ID,
            TEST_ORG_SLUG,
            TEST_UPDATE_TAG,
            common_job_parameters,
            TEST_BASE_URL,
        )


@patch.object(
    cartography.intel.sentry.projects,
    "get",
    return_value=tests.data.sentry.projects.SENTRY_PROJECTS,
)
def test_sync_sentry_projects(mock_api, neo4j_session):
    # Arrange
    _setup_org_and_teams(neo4j_session)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}

    # Act
    cartography.intel.sentry.projects.sync(
        neo4j_session,
        requests.Session(),
        TEST_ORG_ID,
        TEST_ORG_SLUG,
        TEST_UPDATE_TAG,
        common_job_parameters,
        TEST_BASE_URL,
    )

    # Assert projects exist
    assert check_nodes(neo4j_session, "SentryProject", ["id", "slug"]) == {
        ("400", "backend-api"),
        ("401", "frontend-app"),
    }

    # Assert RESOURCE relationship to org
    assert check_rels(
        neo4j_session,
        "SentryProject",
        "id",
        "SentryOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("400", TEST_ORG_ID), ("401", TEST_ORG_ID)}

    # Assert HAS_TEAM relationship
    assert check_rels(
        neo4j_session,
        "SentryProject",
        "id",
        "SentryTeam",
        "id",
        "HAS_TEAM",
        rel_direction_right=True,
    ) == {
        ("400", "200"),  # backend-api -> backend-team
        ("401", "201"),  # frontend-app -> frontend-team
    }
