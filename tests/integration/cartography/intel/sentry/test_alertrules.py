from unittest.mock import patch

import requests

import cartography.intel.sentry.alertrules
import cartography.intel.sentry.organizations
import cartography.intel.sentry.projects
import cartography.intel.sentry.teams
import tests.data.sentry.alertrules
import tests.data.sentry.organizations
import tests.data.sentry.projects
import tests.data.sentry.teams
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "100"
TEST_ORG_SLUG = "simpson-corp"
TEST_BASE_URL = "https://sentry.io/api/0"


def _setup_org_teams_projects(neo4j_session):
    """Create prerequisite org, team, and project nodes."""
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

    with patch.object(
        cartography.intel.sentry.projects,
        "get",
        return_value=tests.data.sentry.projects.SENTRY_PROJECTS,
    ):
        cartography.intel.sentry.projects.sync(
            neo4j_session,
            requests.Session(),
            TEST_ORG_ID,
            TEST_ORG_SLUG,
            TEST_UPDATE_TAG,
            common_job_parameters,
            TEST_BASE_URL,
        )


@patch.object(
    cartography.intel.sentry.alertrules,
    "get",
    return_value=tests.data.sentry.alertrules.SENTRY_ALERT_RULES,
)
def test_sync_sentry_alert_rules(mock_api, neo4j_session):
    # Arrange
    _setup_org_teams_projects(neo4j_session)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}

    project = {"id": "400", "slug": "backend-api"}

    # Act
    cartography.intel.sentry.alertrules.sync(
        neo4j_session,
        requests.Session(),
        TEST_ORG_ID,
        TEST_ORG_SLUG,
        project,
        TEST_UPDATE_TAG,
        TEST_BASE_URL,
    )

    # Assert alert rules exist
    assert check_nodes(neo4j_session, "SentryAlertRule", ["id", "name"]) == {
        ("500", "High Error Rate"),
        ("501", "New Issue Alert"),
    }

    # Assert HAS_RULE relationship to project
    assert check_rels(
        neo4j_session,
        "SentryAlertRule",
        "id",
        "SentryProject",
        "id",
        "HAS_RULE",
        rel_direction_right=False,
    ) == {("500", "400"), ("501", "400")}

    # Assert RESOURCE relationship to org
    assert check_rels(
        neo4j_session,
        "SentryAlertRule",
        "id",
        "SentryOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("500", TEST_ORG_ID), ("501", TEST_ORG_ID)}

    # Act: cleanup at org level
    cartography.intel.sentry.alertrules.cleanup(neo4j_session, common_job_parameters)

    # Assert nodes still exist (same update tag, nothing to clean)
    assert check_nodes(neo4j_session, "SentryAlertRule", ["id"]) == {
        ("500",),
        ("501",),
    }
