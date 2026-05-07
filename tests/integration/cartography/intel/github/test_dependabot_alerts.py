from unittest.mock import patch

import requests

import cartography.intel.github.dependabot_alerts
from cartography.intel.github.dependabot_alerts import DependabotAlertsFetchResult
from tests.data.github.dependabot_alerts import GET_DEPENDABOT_ALERTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://fake.github.net/graphql/"
TEST_ORGANIZATION = "simpsoncorp"
FAKE_API_KEY = "asdf"


def _ensure_org_and_repos_exist(neo4j_session):
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization{id: "https://github.com/simpsoncorp"})
        SET org.username = "simpsoncorp"

        MERGE (repo1:GitHubRepository{id: "https://github.com/simpsoncorp/sample_repo"})
        SET repo1.name = "sample_repo"

        MERGE (repo2:GitHubRepository{id: "https://github.com/simpsoncorp/SampleRepo2"})
        SET repo2.name = "SampleRepo2"

        MERGE (repo1)-[:OWNER]->(org)
        MERGE (repo2)-[:OWNER]->(org)
        """,
    )


def _seed_stale_alert(neo4j_session):
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization{id: "https://github.com/simpsoncorp"})
        MERGE (alert:GitHubDependabotAlert{
            id: "https://github.com/simpsoncorp/sample_repo/security/dependabot/stale"
        })
        SET alert.lastupdated = 1, alert.state = "open"
        MERGE (org)-[:RESOURCE]->(alert)
        """,
    )


@patch.object(
    cartography.intel.github.dependabot_alerts,
    "get",
    return_value=DependabotAlertsFetchResult(
        alerts=GET_DEPENDABOT_ALERTS,
        cleanup_safe=True,
    ),
)
def test_sync_github_dependabot_alerts(mock_get, neo4j_session):
    _ensure_org_and_repos_exist(neo4j_session)

    cartography.intel.github.dependabot_alerts.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    assert check_nodes(
        neo4j_session,
        "GitHubDependabotAlert",
        [
            "id",
            "state",
            "dependency_package_ecosystem",
            "dependency_package_name",
            "severity",
            "advisory_cve_id",
        ],
    ) == {
        (
            "https://github.com/simpsoncorp/sample_repo/security/dependabot/1",
            "open",
            "pip",
            "django",
            "high",
            "CVE-2018-6188",
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/security/dependabot/2",
            "dismissed",
            "npm",
            "lodash",
            "critical",
            "CVE-2019-10744",
        ),
        (
            "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/3",
            "fixed",
            "pip",
            "ansible",
            "medium",
            "CVE-2021-20191",
        ),
        (
            "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/4",
            "auto_dismissed",
            "rubygems",
            "rack",
            "low",
            None,
        ),
    }

    assert {
        ("https://github.com/hjsimpson", "hjsimpson"),
        ("https://github.com/mbsimpson", "mbsimpson"),
    }.issubset(check_nodes(neo4j_session, "GitHubUser", ["id", "username"]))

    assert check_rels(
        neo4j_session,
        "GitHubDependabotAlert",
        "id",
        "GitHubOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (
            "https://github.com/simpsoncorp/sample_repo/security/dependabot/1",
            "https://github.com/simpsoncorp",
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/security/dependabot/2",
            "https://github.com/simpsoncorp",
        ),
        (
            "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/3",
            "https://github.com/simpsoncorp",
        ),
        (
            "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/4",
            "https://github.com/simpsoncorp",
        ),
    }

    assert check_rels(
        neo4j_session,
        "GitHubDependabotAlert",
        "id",
        "GitHubRepository",
        "id",
        "FOUND_IN",
        rel_direction_right=True,
    ) == {
        (
            "https://github.com/simpsoncorp/sample_repo/security/dependabot/1",
            "https://github.com/simpsoncorp/sample_repo",
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/security/dependabot/2",
            "https://github.com/simpsoncorp/sample_repo",
        ),
        (
            "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/3",
            "https://github.com/simpsoncorp/SampleRepo2",
        ),
        (
            "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/4",
            "https://github.com/simpsoncorp/SampleRepo2",
        ),
    }

    assert check_rels(
        neo4j_session,
        "GitHubDependabotAlert",
        "id",
        "GitHubUser",
        "id",
        "DISMISSED_BY",
        rel_direction_right=True,
    ) == {
        (
            "https://github.com/simpsoncorp/sample_repo/security/dependabot/2",
            "https://github.com/hjsimpson",
        ),
    }

    assert check_rels(
        neo4j_session,
        "GitHubDependabotAlert",
        "id",
        "GitHubUser",
        "id",
        "ASSIGNED_TO",
        rel_direction_right=True,
    ) == {
        (
            "https://github.com/simpsoncorp/sample_repo/security/dependabot/1",
            "https://github.com/mbsimpson",
        ),
    }


@patch.object(
    cartography.intel.github.dependabot_alerts,
    "get",
    return_value=DependabotAlertsFetchResult(alerts=[], cleanup_safe=True),
)
def test_sync_github_dependabot_alerts_empty_response_cleans_stale_alerts(
    mock_get,
    neo4j_session,
):
    _seed_stale_alert(neo4j_session)

    cartography.intel.github.dependabot_alerts.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    assert check_nodes(neo4j_session, "GitHubDependabotAlert", ["id"]) == set()


@patch.object(
    cartography.intel.github.dependabot_alerts,
    "get",
    return_value=DependabotAlertsFetchResult(alerts=[], cleanup_safe=False),
)
def test_sync_github_dependabot_alerts_unsafe_fetch_skips_cleanup(
    mock_get,
    neo4j_session,
):
    _seed_stale_alert(neo4j_session)

    cartography.intel.github.dependabot_alerts.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    assert check_nodes(neo4j_session, "GitHubDependabotAlert", ["id"]) == {
        ("https://github.com/simpsoncorp/sample_repo/security/dependabot/stale",),
    }


@patch.object(
    cartography.intel.github.dependabot_alerts,
    "fetch_all_rest_api_pages",
    return_value=[],
)
def test_get_dependabot_alerts_uses_org_endpoint_and_api_version(mock_fetch):
    result = cartography.intel.github.dependabot_alerts.get(
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    assert result == DependabotAlertsFetchResult(alerts=[], cleanup_safe=True)
    mock_fetch.assert_called_once_with(
        FAKE_API_KEY,
        "https://fake.github.net/api/v3",
        "/orgs/simpsoncorp/dependabot/alerts",
        "",
        params={
            "state": "open,fixed,dismissed,auto_dismissed",
            "per_page": 100,
        },
        raise_on_status=(403, 404),
        api_version="2026-03-10",
    )


@patch.object(
    cartography.intel.github.dependabot_alerts,
    "fetch_all_rest_api_pages",
)
def test_get_dependabot_alerts_marks_403_fetch_as_not_cleanup_safe(mock_fetch):
    response = requests.Response()
    response.status_code = 403
    mock_fetch.side_effect = requests.exceptions.HTTPError(response=response)

    result = cartography.intel.github.dependabot_alerts.get(
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    assert result == DependabotAlertsFetchResult(alerts=[], cleanup_safe=False)
