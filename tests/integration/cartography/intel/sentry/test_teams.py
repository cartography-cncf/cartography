from unittest.mock import patch

import requests

import cartography.intel.sentry.organizations
import cartography.intel.sentry.teams
import tests.data.sentry.organizations
import tests.data.sentry.teams
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "100"
TEST_ORG_SLUG = "simpson-corp"
TEST_BASE_URL = "https://sentry.io/api/0"


@patch.object(
    cartography.intel.sentry.organizations,
    "get",
    return_value=tests.data.sentry.organizations.SENTRY_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.sentry.teams,
    "get",
    return_value=tests.data.sentry.teams.SENTRY_TEAMS,
)
def test_sync_sentry_teams(mock_teams, mock_orgs, neo4j_session):
    # Arrange: create org
    cartography.intel.sentry.organizations.sync(
        neo4j_session,
        requests.Session(),
        TEST_UPDATE_TAG,
        TEST_BASE_URL,
    )

    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}

    # Act
    cartography.intel.sentry.teams.sync(
        neo4j_session,
        requests.Session(),
        TEST_ORG_ID,
        TEST_ORG_SLUG,
        TEST_UPDATE_TAG,
        common_job_parameters,
        TEST_BASE_URL,
    )

    # Assert teams exist
    assert check_nodes(neo4j_session, "SentryTeam", ["id", "slug"]) == {
        ("200", "backend-team"),
        ("201", "frontend-team"),
    }

    # Assert UserGroup semantic label
    assert check_nodes(neo4j_session, "UserGroup", ["id"]) == {
        ("200",),
        ("201",),
    }

    # Assert RESOURCE relationship to org
    assert check_rels(
        neo4j_session,
        "SentryTeam",
        "id",
        "SentryOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("200", TEST_ORG_ID), ("201", TEST_ORG_ID)}
