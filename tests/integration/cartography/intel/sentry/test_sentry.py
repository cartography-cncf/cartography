from unittest.mock import patch

import pytest
import requests

import cartography.intel.sentry.alertrules
import cartography.intel.sentry.members
import cartography.intel.sentry.organizations
import cartography.intel.sentry.projects
import cartography.intel.sentry.releases
import cartography.intel.sentry.teams
import tests.data.sentry.alertrules
import tests.data.sentry.members
import tests.data.sentry.organizations
import tests.data.sentry.projects
import tests.data.sentry.releases
import tests.data.sentry.teams
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "100"
TEST_ORG_SLUG = "simpson-corp"
TEST_BASE_URL = "https://sentry.io/api/0"


@pytest.fixture(scope="module")
def synced_org_teams_projects(neo4j_session):
    """
    Sync the Sentry organization, teams and projects once for the module.
    The tests below add disjoint labels on top of this graph with the same update
    tag, so none of them removes what another test reads.
    """
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}

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


def test_sync_sentry_org_teams_projects(neo4j_session, synced_org_teams_projects):
    # Arrange and act: done by the synced_org_teams_projects fixture

    # Assert organization exists
    assert check_nodes(neo4j_session, "SentryOrganization", ["id", "slug"]) == {
        ("100", "simpson-corp"),
    }

    # Assert Tenant semantic label
    assert check_nodes(neo4j_session, "Tenant", ["id"]) == {
        ("100",),
    }

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

    # Assert team RESOURCE relationship to org
    assert check_rels(
        neo4j_session,
        "SentryTeam",
        "id",
        "SentryOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("200", TEST_ORG_ID), ("201", TEST_ORG_ID)}

    # Assert projects exist
    assert check_nodes(neo4j_session, "SentryProject", ["id", "slug"]) == {
        ("400", "backend-api"),
        ("401", "frontend-app"),
    }

    # Assert project RESOURCE relationship to org
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
def test_sync_sentry_members(
    mock_get, mock_memberships, neo4j_session, synced_org_teams_projects
):
    # Arrange
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


@patch.object(
    cartography.intel.sentry.releases,
    "get",
    return_value=tests.data.sentry.releases.SENTRY_RELEASES,
)
def test_sync_sentry_releases(mock_releases, neo4j_session, synced_org_teams_projects):
    # Arrange
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}

    # Act
    cartography.intel.sentry.releases.sync(
        neo4j_session,
        requests.Session(),
        TEST_ORG_ID,
        TEST_ORG_SLUG,
        TEST_UPDATE_TAG,
        common_job_parameters,
        TEST_BASE_URL,
    )

    # Assert releases exist (id is org_id/version to avoid cross-org collisions)
    assert check_nodes(neo4j_session, "SentryRelease", ["id", "version"]) == {
        (f"{TEST_ORG_ID}/backend-api@1.0.0", "backend-api@1.0.0"),
        (f"{TEST_ORG_ID}/frontend-app@2.0.0", "frontend-app@2.0.0"),
    }

    # Assert RESOURCE relationship to org
    assert check_rels(
        neo4j_session,
        "SentryRelease",
        "id",
        "SentryOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (f"{TEST_ORG_ID}/backend-api@1.0.0", TEST_ORG_ID),
        (f"{TEST_ORG_ID}/frontend-app@2.0.0", TEST_ORG_ID),
    }


@patch.object(
    cartography.intel.sentry.alertrules,
    "get",
    return_value=tests.data.sentry.alertrules.SENTRY_ALERT_RULES,
)
def test_sync_sentry_alert_rules(mock_api, neo4j_session, synced_org_teams_projects):
    # Arrange
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
