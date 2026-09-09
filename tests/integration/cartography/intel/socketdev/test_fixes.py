from unittest.mock import patch

import cartography.intel.socketdev.fixes
import tests.data.socketdev.fixes
from cartography.intel.socketdev.alerts import load_alerts
from cartography.intel.socketdev.alerts import transform as transform_alerts
from cartography.intel.socketdev.dependencies import load_dependencies
from cartography.intel.socketdev.dependencies import transform as transform_deps
from cartography.intel.socketdev.organizations import load_organizations
from cartography.intel.socketdev.organizations import transform as transform_orgs
from cartography.intel.socketdev.repositories import load_repositories
from cartography.intel.socketdev.repositories import transform as transform_repos
from tests.data.socketdev.alerts import ALERTS_RESPONSE
from tests.data.socketdev.dependencies import DEPENDENCIES_RESPONSE
from tests.data.socketdev.organizations import ORGANIZATIONS_RESPONSE
from tests.data.socketdev.repositories import REPOSITORIES_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "org-001"
TEST_ORG_SLUG = "acme-corp"


@patch.object(
    cartography.intel.socketdev.fixes,
    "get",
    return_value=tests.data.socketdev.fixes.FIXES_RESPONSE,
)
def test_sync_fixes(mock_api, neo4j_session):
    """
    Test that Socket.dev fixes sync correctly and create proper nodes and relationships.
    """
    # Arrange: Load org, repos, dependencies, and alerts first
    orgs = transform_orgs(ORGANIZATIONS_RESPONSE)
    load_organizations(neo4j_session, orgs, TEST_UPDATE_TAG)

    repos = transform_repos(REPOSITORIES_RESPONSE["results"])
    load_repositories(neo4j_session, repos, TEST_ORG_ID, TEST_UPDATE_TAG)

    deps = transform_deps(DEPENDENCIES_RESPONSE["rows"])
    load_dependencies(neo4j_session, deps, TEST_ORG_ID, TEST_UPDATE_TAG)

    alerts = transform_alerts(ALERTS_RESPONSE["items"])
    load_alerts(neo4j_session, alerts, TEST_ORG_ID, TEST_UPDATE_TAG)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
        "ORG_SLUG": TEST_ORG_SLUG,
    }

    # Act
    cartography.intel.socketdev.fixes.sync_fixes(
        neo4j_session,
        "fake-token",
        TEST_ORG_SLUG,
        TEST_UPDATE_TAG,
        common_job_parameters,
        alerts=alerts,
        dependencies=deps,
    )

    # Assert: Fix nodes exist
    expected_fix_nodes = {
        ("GHSA-xxxx-yyyy-zzzz|pkg:npm/lodash@4.17.21|4.17.22", "4.17.22", "fixFound"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SocketDevFix",
            ["id", "fixed_version", "fix_type"],
        )
        == expected_fix_nodes
    )

    # Assert: Fix has the semantic label "Fix"
    result = neo4j_session.run(
        "MATCH (f:Fix:SocketDevFix) RETURN count(f) AS count",
    ).single()
    assert result["count"] == 1

    # Assert: Fix is connected to Organization
    expected_org_rels = {
        ("GHSA-xxxx-yyyy-zzzz|pkg:npm/lodash@4.17.21|4.17.22", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "SocketDevFix",
            "id",
            "SocketDevOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_org_rels
    )

    # Assert: Fix APPLIES_TO Alert
    expected_alert_rels = {
        ("GHSA-xxxx-yyyy-zzzz|pkg:npm/lodash@4.17.21|4.17.22", "alert-001"),
    }
    assert (
        check_rels(
            neo4j_session,
            "SocketDevFix",
            "id",
            "SocketDevAlert",
            "id",
            "APPLIES_TO",
            rel_direction_right=True,
        )
        == expected_alert_rels
    )

    # Assert: Dependency SHOULD_UPDATE_TO Fix
    expected_dep_rels = {
        ("dep-001", "GHSA-xxxx-yyyy-zzzz|pkg:npm/lodash@4.17.21|4.17.22"),
    }
    assert (
        check_rels(
            neo4j_session,
            "SocketDevDependency",
            "id",
            "SocketDevFix",
            "id",
            "SHOULD_UPDATE_TO",
            rel_direction_right=True,
        )
        == expected_dep_rels
    )
