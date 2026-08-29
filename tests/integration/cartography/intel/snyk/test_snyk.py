from unittest.mock import patch

import cartography.intel.snyk
import cartography.intel.snyk.issues
import cartography.intel.snyk.orgs
import cartography.intel.snyk.projects
import cartography.intel.snyk.targets
from cartography.config import Config
from tests.data.snyk.data import ISSUE_ADVISORY_ID
from tests.data.snyk.data import ISSUE_CVE_ID
from tests.data.snyk.data import ISSUES
from tests.data.snyk.data import ORG
from tests.data.snyk.data import ORG_ID
from tests.data.snyk.data import ORG_STALE
from tests.data.snyk.data import ORG_STALE_ID
from tests.data.snyk.data import PROJECT_ID
from tests.data.snyk.data import PROJECTS
from tests.data.snyk.data import TARGET_ID
from tests.data.snyk.data import TARGETS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _config(update_tag=TEST_UPDATE_TAG):
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        snyk_api_key="test-token",
        snyk_org_id=ORG_ID,
    )


@patch.object(cartography.intel.snyk, "build_session")
@patch.object(cartography.intel.snyk.issues, "get", return_value=ISSUES)
@patch.object(cartography.intel.snyk.projects, "get", return_value=PROJECTS)
@patch.object(cartography.intel.snyk.targets, "get", return_value=TARGETS)
@patch.object(cartography.intel.snyk.orgs, "get", return_value=ORG)
def test_start_snyk_ingestion(
    _mock_org,
    _mock_targets,
    _mock_projects,
    _mock_issues,
    mock_build_session,
    neo4j_session,
):
    mock_build_session.return_value = object()

    cartography.intel.snyk.start_snyk_ingestion(neo4j_session, _config())

    assert check_nodes(neo4j_session, "SnykOrg", ["id", "name"]) == {
        (ORG_ID, "Example Org")
    }
    assert check_nodes(neo4j_session, "Tenant", ["id"]) == {(ORG_ID,)}
    assert check_nodes(neo4j_session, "SnykTarget", ["id", "display_name"]) == {
        (TARGET_ID, "example/app")
    }
    assert check_nodes(neo4j_session, "SnykProject", ["id", "name"]) == {
        (PROJECT_ID, "example/app:Dockerfile")
    }
    assert check_nodes(neo4j_session, "SnykIssue", ["id", "title"]) == {
        (ISSUE_CVE_ID, "Prototype Pollution in minimist"),
        (ISSUE_ADVISORY_ID, "License policy issue"),
    }
    assert (ISSUE_CVE_ID,) in check_nodes(neo4j_session, "CVE", ["id"])
    assert (ISSUE_ADVISORY_ID,) in check_nodes(neo4j_session, "SecurityIssue", ["id"])

    assert check_rels(
        neo4j_session,
        "SnykOrg",
        "id",
        "SnykTarget",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {(ORG_ID, TARGET_ID)}
    assert check_rels(
        neo4j_session,
        "SnykOrg",
        "id",
        "SnykProject",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {(ORG_ID, PROJECT_ID)}
    assert check_rels(
        neo4j_session,
        "SnykProject",
        "id",
        "SnykTarget",
        "id",
        "MONITORS",
        rel_direction_right=True,
    ) == {(PROJECT_ID, TARGET_ID)}
    assert check_rels(
        neo4j_session,
        "SnykIssue",
        "id",
        "SnykProject",
        "id",
        "FOUND_IN",
        rel_direction_right=True,
    ) == {
        (ISSUE_CVE_ID, PROJECT_ID),
        (ISSUE_ADVISORY_ID, PROJECT_ID),
    }


@patch.object(cartography.intel.snyk, "build_session")
@patch.object(cartography.intel.snyk.issues, "get")
@patch.object(cartography.intel.snyk.projects, "get")
@patch.object(cartography.intel.snyk.targets, "get")
@patch.object(cartography.intel.snyk.orgs, "get", return_value=ORG)
def test_start_snyk_ingestion_cleans_stale_resources(
    _mock_org,
    mock_targets,
    mock_projects,
    mock_issues,
    mock_build_session,
    neo4j_session,
):
    mock_build_session.return_value = object()
    mock_targets.return_value = TARGETS
    mock_projects.return_value = PROJECTS
    mock_issues.return_value = ISSUES
    cartography.intel.snyk.start_snyk_ingestion(neo4j_session, _config())

    mock_targets.return_value = []
    mock_projects.return_value = []
    mock_issues.return_value = []
    cartography.intel.snyk.start_snyk_ingestion(
        neo4j_session, _config(update_tag=TEST_UPDATE_TAG + 1)
    )

    assert check_nodes(neo4j_session, "SnykOrg", ["id"]) == {(ORG_ID,)}
    assert check_nodes(neo4j_session, "SnykTarget", ["id"]) == set()
    assert check_nodes(neo4j_session, "SnykProject", ["id"]) == set()
    assert check_nodes(neo4j_session, "SnykIssue", ["id"]) == set()


@patch.object(cartography.intel.snyk, "build_session")
@patch.object(cartography.intel.snyk.issues, "get", return_value=[])
@patch.object(cartography.intel.snyk.projects, "get", return_value=[])
@patch.object(cartography.intel.snyk.targets, "get", return_value=[])
@patch.object(cartography.intel.snyk.orgs, "get")
def test_start_snyk_ingestion_keeps_other_org_runs_isolated(
    mock_org,
    _mock_targets,
    _mock_projects,
    _mock_issues,
    mock_build_session,
    neo4j_session,
):
    mock_build_session.return_value = object()
    mock_org.return_value = ORG_STALE
    stale_config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        snyk_api_key="test-token",
        snyk_org_id=ORG_STALE_ID,
    )
    cartography.intel.snyk.start_snyk_ingestion(neo4j_session, stale_config)

    mock_org.return_value = ORG
    cartography.intel.snyk.start_snyk_ingestion(
        neo4j_session, _config(update_tag=TEST_UPDATE_TAG + 1)
    )

    assert check_nodes(neo4j_session, "SnykOrg", ["id"]) == {
        (ORG_ID,),
        (ORG_STALE_ID,),
    }
