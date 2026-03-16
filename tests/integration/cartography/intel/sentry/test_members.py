from unittest.mock import patch

import requests

import cartography.intel.sentry.members
import cartography.intel.sentry.organizations
import cartography.intel.sentry.teams
import tests.data.sentry.members
import tests.data.sentry.organizations
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
    cartography.intel.sentry.members,
    "_get_team_memberships",
    return_value=tests.data.sentry.members.SENTRY_TEAM_MEMBERSHIPS,
)
@patch.object(
    cartography.intel.sentry.members,
    "get",
    return_value=tests.data.sentry.members.SENTRY_MEMBERS,
)
def test_sync_sentry_members(mock_get, mock_memberships, neo4j_session):
    # Arrange
    _setup_org_and_teams(neo4j_session)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}
    teams = cartography.intel.sentry.teams.transform(
        tests.data.sentry.teams.SENTRY_TEAMS
    )

    # Act
    cartography.intel.sentry.members.sync(
        neo4j_session,
        requests.Session(),
        TEST_ORG_ID,
        TEST_ORG_SLUG,
        TEST_UPDATE_TAG,
        common_job_parameters,
        TEST_BASE_URL,
        teams,
    )

    # Assert members exist
    assert check_nodes(neo4j_session, "SentryUser", ["id", "email"]) == {
        ("300", "mbsimpson@simpson.corp"),
        ("301", "hjsimpson@simpson.corp"),
    }

    # Assert UserAccount semantic label
    expected_user_accounts = {("300",), ("301",)}
    assert check_nodes(neo4j_session, "UserAccount", ["id"]) == expected_user_accounts

    # Assert RESOURCE relationship to org
    assert check_rels(
        neo4j_session,
        "SentryUser",
        "id",
        "SentryOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("300", TEST_ORG_ID), ("301", TEST_ORG_ID)}

    # Assert MEMBER_OF relationship to teams
    # Marge (owner) -> all teams, Homer -> both teams
    assert check_rels(
        neo4j_session,
        "SentryUser",
        "id",
        "SentryTeam",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        ("300", "200"),  # Marge (owner) -> backend-team
        ("300", "201"),  # Marge (owner) -> frontend-team
        ("301", "200"),  # Homer -> backend-team
        ("301", "201"),  # Homer -> frontend-team
    }

    # Assert ADMIN_OF relationship to teams
    # Marge (owner) -> admin of all teams, Homer -> admin of backend only
    assert check_rels(
        neo4j_session,
        "SentryUser",
        "id",
        "SentryTeam",
        "id",
        "ADMIN_OF",
        rel_direction_right=True,
    ) == {
        ("300", "200"),  # Marge (owner) -> backend-team
        ("300", "201"),  # Marge (owner) -> frontend-team
        ("301", "200"),  # Homer -> admin of backend-team
    }
