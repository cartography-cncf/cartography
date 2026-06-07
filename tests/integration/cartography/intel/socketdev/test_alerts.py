from unittest.mock import patch

import cartography.intel.socketdev.alerts
import tests.data.socketdev.alerts
from cartography.intel.socketdev.organizations import load_organizations
from cartography.intel.socketdev.organizations import transform as transform_orgs
from cartography.intel.socketdev.repositories import load_repositories
from cartography.intel.socketdev.repositories import transform as transform_repos
from tests.data.socketdev.organizations import ORGANIZATIONS_RESPONSE
from tests.data.socketdev.repositories import REPOSITORIES_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "org-001"
TEST_ORG_SLUG = "acme-corp"


@patch.object(
    cartography.intel.socketdev.alerts,
    "get",
    return_value=tests.data.socketdev.alerts.ALERTS_RESPONSE["items"],
)
def test_sync_alerts(mock_api, neo4j_session):
    """
    Test that Socket.dev alerts sync correctly and create proper nodes and relationships.
    """
    # Arrange: Load org and repos first
    orgs = transform_orgs(ORGANIZATIONS_RESPONSE)
    load_organizations(neo4j_session, orgs, TEST_UPDATE_TAG)

    repos = transform_repos(REPOSITORIES_RESPONSE["results"])
    load_repositories(neo4j_session, repos, TEST_ORG_ID, TEST_UPDATE_TAG)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
        "ORG_SLUG": TEST_ORG_SLUG,
    }

    # Act
    cartography.intel.socketdev.alerts.sync_alerts(
        neo4j_session,
        "fake-token",
        TEST_ORG_SLUG,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: Alerts exist with correct properties
    expected_alert_nodes = {
        ("alert-001", "criticalCVE", "vulnerability", "critical"),
        ("alert-002", "malware", "supplyChainRisk", "critical"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SocketDevAlert",
            ["id", "type", "category", "severity"],
        )
        == expected_alert_nodes
    )

    # Assert: Alerts are connected to Organization
    expected_org_rels = {
        ("alert-001", TEST_ORG_ID),
        ("alert-002", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "SocketDevAlert",
            "id",
            "SocketDevOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_org_rels
    )

    # Assert: Alerts are connected to Repositories
    expected_repo_rels = {
        ("alert-001", "acme-corp/frontend-app"),
        ("alert-002", "acme-corp/backend-api"),
    }
    assert (
        check_rels(
            neo4j_session,
            "SocketDevAlert",
            "id",
            "SocketDevRepository",
            "fullname",
            "FOUND_IN",
            rel_direction_right=True,
        )
        == expected_repo_rels
    )

    # Assert: Vulnerability-specific fields are populated
    result = neo4j_session.run(
        "MATCH (a:SocketDevAlert {id: 'alert-001'}) "
        "RETURN a.cve_id AS cve_id, a.ghsa_id AS ghsa_id, "
        "a.cvss_score AS cvss_score, "
        "a.is_kev AS is_kev, a.epss_score AS epss_score",
    ).single()
    assert result["cve_id"] is None
    assert result["ghsa_id"] == "GHSA-xxxx-yyyy-zzzz"
    assert result["cvss_score"] == 9.8
    assert result["is_kev"] is True
    assert result["epss_score"] == 0.85
