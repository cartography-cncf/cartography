from unittest.mock import patch

import requests

import cartography.intel.github.dependabot_alerts
from cartography.intel.cve_metadata import get_cve_ids_from_graph
from cartography.intel.github.dependabot_alerts import DependabotAlertsFetchResult
from tests.data.github.dependabot_alerts import GET_DEPENDABOT_ALERTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://api.github.com/graphql"
TEST_GITHUB_ENTERPRISE_URL = "https://fake.github.net/graphql/"
TEST_ORGANIZATION = "simpsoncorp"
FAKE_API_KEY = "asdf"


def _clear_dependabot_alerts(neo4j_session):
    neo4j_session.run(
        "MATCH (n) WHERE n:GitHubDependabotAlert OR n:GitHubSecurityAdvisory "
        "DETACH DELETE n"
    )


def _ensure_org_and_repos_exist(neo4j_session):
    _clear_dependabot_alerts(neo4j_session)
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


def _ensure_enterprise_org_and_repos_exist(neo4j_session):
    _clear_dependabot_alerts(neo4j_session)
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization{id: "https://fake.github.net/simpsoncorp"})
        SET org.username = "simpsoncorp"

        MERGE (repo1:GitHubRepository{id: "https://github.com/simpsoncorp/sample_repo"})
        SET repo1.name = "sample_repo"

        MERGE (repo2:GitHubRepository{id: "https://github.com/simpsoncorp/SampleRepo2"})
        SET repo2.name = "SampleRepo2"
        """,
    )


def _seed_alerts_from_earlier_versions(neo4j_session):
    # Earlier versions labeled an alert :CVE when its advisory had a CVE, wrote the
    # CVE _ont_* fields on every alert, and CVEMetadata enriched the :CVE ones. The
    # other organization has not synced since.
    neo4j_session.run(
        """
        MATCH (org:GitHubOrganization {id: "https://github.com/simpsoncorp"})
        MERGE (org)-[:RESOURCE]->(cve_alert:GitHubDependabotAlert:CVE {
            id: "https://github.com/simpsoncorp/sample_repo/security/dependabot/1"
        })
        SET cve_alert._ont_source = "github",
            cve_alert._ont_cve_id = "CVE-2018-6188",
            cve_alert._ont_description = "Django allows remote attackers to obtain information."
        MERGE (org)-[:RESOURCE]->(ghsa_alert:GitHubDependabotAlert {
            id: "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/4"
        })
        SET ghsa_alert._ont_source = "github"
        MERGE (other:GitHubOrganization {id: "https://github.com/otherorg"})
        MERGE (other)-[:RESOURCE]->(other_alert:GitHubDependabotAlert:CVE {
            id: "https://github.com/otherorg/repo/security/dependabot/1"
        })
        MERGE (metadata:CVEMetadata {id: "CVE-2018-6188"})
        MERGE (metadata)-[:ENRICHES]->(cve_alert)
        MERGE (metadata)-[:ENRICHES]->(other_alert)
        """,
    )


def _seed_stale_alert(neo4j_session):
    _clear_dependabot_alerts(neo4j_session)
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


def _seed_enterprise_stale_alert(neo4j_session):
    _clear_dependabot_alerts(neo4j_session)
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization{id: "https://fake.github.net/simpsoncorp"})
        MERGE (alert:GitHubDependabotAlert{
            id: "https://fake.github.net/simpsoncorp/sample_repo/security/dependabot/stale"
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
    _seed_alerts_from_earlier_versions(neo4j_session)

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
            "cve_id",
        ],
    ) == {
        (
            "https://github.com/simpsoncorp/sample_repo/security/dependabot/1",
            "open",
            "pip",
            "django",
            "high",
            "CVE-2018-6188",
            "CVE-2018-6188",
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/security/dependabot/2",
            "dismissed",
            "npm",
            "lodash",
            "critical",
            "CVE-2019-10744",
            "CVE-2019-10744",
        ),
        (
            "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/3",
            "fixed",
            "pip",
            "ansible",
            "medium",
            "CVE-2021-20191",
            "CVE-2021-20191",
        ),
        (
            "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/4",
            "auto_dismissed",
            "rubygems",
            "rack",
            "low",
            None,
            None,
        ),
        (
            "https://github.com/otherorg/repo/security/dependabot/1",
            None,
            None,
            None,
            None,
            None,
            None,
        ),
    }

    assert {
        (
            "GHSA|GHSA-rf4j-j272-fj86",
            "CVE-2018-6188",
            7.5,
            "high",
            "Django allows remote attackers to obtain information.",
            "2018-10-03T21:13:54Z",
            "2022-04-26T18:35:37Z",
            "CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
            "github",
        ),
        (
            "GHSA|GHSA-35jh-r3h4-6jhm",
            "CVE-2019-10744",
            9.8,
            "critical",
            "Prototype pollution in lodash.",
            None,
            None,
            "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            "github",
        ),
        (
            "GHSA|GHSA-8f4m-hccc-8qph",
            "CVE-2021-20191",
            None,
            "medium",
            "Sensitive information may be logged.",
            None,
            None,
            None,
            "github",
        ),
    }.issubset(
        check_nodes(
            neo4j_session,
            "CVE",
            [
                "id",
                "_ont_cve_id",
                "_ont_base_score",
                "_ont_base_severity",
                "_ont_description",
                "_ont_published_date",
                "_ont_last_modified_date",
                "_ont_vector_string",
                "_ont_source",
            ],
        )
    )
    assert set(get_cve_ids_from_graph(neo4j_session)).issuperset(
        {
            "CVE-2018-6188",
            "CVE-2019-10744",
            "CVE-2021-20191",
        }
    )
    ghsa_only_has_cve_label = neo4j_session.run(
        """
        MATCH (advisory:GitHubSecurityAdvisory {id: "GHSA|GHSA-test-auto"})
        RETURN "CVE" IN labels(advisory) AS has_cve_label
        """,
    ).single()
    assert ghsa_only_has_cve_label["has_cve_label"] is False

    # Each alert links to its advisory, which is the :CVE node, so CVEMetadata
    # enriches each advisory once instead of every alert that reports it.
    assert check_rels(
        neo4j_session,
        "GitHubDependabotAlert",
        "id",
        "GitHubSecurityAdvisory",
        "id",
        "HAS_VULNERABILITY",
        rel_direction_right=True,
    ) == {
        (
            "https://github.com/simpsoncorp/sample_repo/security/dependabot/1",
            "GHSA|GHSA-rf4j-j272-fj86",
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/security/dependabot/2",
            "GHSA|GHSA-35jh-r3h4-6jhm",
        ),
        (
            "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/3",
            "GHSA|GHSA-8f4m-hccc-8qph",
        ),
        (
            "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/4",
            "GHSA|GHSA-test-auto",
        ),
    }
    assert check_rels(
        neo4j_session,
        "GitHubSecurityAdvisory",
        "id",
        "GitHubOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("GHSA|GHSA-rf4j-j272-fj86", "https://github.com/simpsoncorp"),
        ("GHSA|GHSA-35jh-r3h4-6jhm", "https://github.com/simpsoncorp"),
        ("GHSA|GHSA-8f4m-hccc-8qph", "https://github.com/simpsoncorp"),
        ("GHSA|GHSA-test-auto", "https://github.com/simpsoncorp"),
    }

    # The sync strips the CVE label, its _ont_* fields, and its enrichment edges
    # from the organization's alerts stored by earlier versions, and leaves the
    # other organization's alert until that organization syncs.
    assert (
        neo4j_session.run(
            """
        MATCH (alert:GitHubDependabotAlert)
        RETURN alert.id AS id, "CVE" IN labels(alert) AS has_cve_label,
               [k IN keys(alert) WHERE k STARTS WITH "_ont_"] AS ont_fields,
               COUNT { (alert)<-[:ENRICHES]-(:CVEMetadata) } AS enrichments
        ORDER BY id
        """,
        ).data()
        == [
            {
                "id": "https://github.com/otherorg/repo/security/dependabot/1",
                "has_cve_label": True,
                "ont_fields": [],
                "enrichments": 1,
            },
            {
                "id": "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/3",
                "has_cve_label": False,
                "ont_fields": [],
                "enrichments": 0,
            },
            {
                "id": "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/4",
                "has_cve_label": False,
                "ont_fields": [],
                "enrichments": 0,
            },
            {
                "id": "https://github.com/simpsoncorp/sample_repo/security/dependabot/1",
                "has_cve_label": False,
                "ont_fields": [],
                "enrichments": 0,
            },
            {
                "id": "https://github.com/simpsoncorp/sample_repo/security/dependabot/2",
                "has_cve_label": False,
                "ont_fields": [],
                "enrichments": 0,
            },
        ]
    )

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
        (
            "https://github.com/otherorg/repo/security/dependabot/1",
            "https://github.com/otherorg",
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
    return_value=DependabotAlertsFetchResult(
        alerts=GET_DEPENDABOT_ALERTS,
        cleanup_safe=True,
    ),
)
def test_sync_github_dependabot_alerts_uses_enterprise_org_url(mock_get, neo4j_session):
    _ensure_enterprise_org_and_repos_exist(neo4j_session)

    cartography.intel.github.dependabot_alerts.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_ENTERPRISE_URL,
        TEST_ORGANIZATION,
    )

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
            "https://fake.github.net/simpsoncorp",
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/security/dependabot/2",
            "https://fake.github.net/simpsoncorp",
        ),
        (
            "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/3",
            "https://fake.github.net/simpsoncorp",
        ),
        (
            "https://github.com/simpsoncorp/SampleRepo2/security/dependabot/4",
            "https://fake.github.net/simpsoncorp",
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
    return_value=DependabotAlertsFetchResult(alerts=[], cleanup_safe=True),
)
def test_sync_github_dependabot_alerts_enterprise_cleanup_uses_enterprise_org_url(
    mock_get,
    neo4j_session,
):
    _seed_enterprise_stale_alert(neo4j_session)

    cartography.intel.github.dependabot_alerts.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_ENTERPRISE_URL,
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
def test_get_dependabot_alerts_uses_public_github_api_version(mock_fetch):
    result = cartography.intel.github.dependabot_alerts.get(
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    assert result == DependabotAlertsFetchResult(alerts=[], cleanup_safe=True)
    mock_fetch.assert_called_once_with(
        FAKE_API_KEY,
        "https://api.github.com",
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
    return_value=[],
)
def test_get_dependabot_alerts_uses_enterprise_default_api_version(mock_fetch):
    result = cartography.intel.github.dependabot_alerts.get(
        FAKE_API_KEY,
        TEST_GITHUB_ENTERPRISE_URL,
        TEST_ORGANIZATION,
    )

    assert result == DependabotAlertsFetchResult(alerts=[], cleanup_safe=True)
    mock_fetch.assert_called_once_with(
        FAKE_API_KEY,
        "https://fake.github.net/v3",
        "/orgs/simpsoncorp/dependabot/alerts",
        "",
        params={
            "state": "open,fixed,dismissed,auto_dismissed",
            "per_page": 100,
        },
        raise_on_status=(403, 404),
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
