from unittest.mock import patch

import cartography.intel.endorlabs.findings
import tests.data.endorlabs.findings
from cartography.client.core.tx import load
from cartography.intel.endorlabs.projects import load_projects
from cartography.intel.endorlabs.projects import transform as transform_projects
from cartography.models.endorlabs.namespace import EndorLabsNamespaceSchema
from tests.data.endorlabs.projects import PROJECTS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_NAMESPACE = "acme-corp"


def _load_namespace(neo4j_session):
    load(
        neo4j_session,
        EndorLabsNamespaceSchema(),
        [{"id": TEST_NAMESPACE, "name": TEST_NAMESPACE}],
        lastupdated=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.endorlabs.findings,
    "get",
    return_value=tests.data.endorlabs.findings.FINDINGS_RESPONSE["list"]["objects"],
)
def test_sync_findings(mock_api, neo4j_session):
    # Arrange: Load namespace and projects first
    _load_namespace(neo4j_session)
    projects = transform_projects(PROJECTS_RESPONSE["list"]["objects"])
    load_projects(neo4j_session, projects, TEST_NAMESPACE, TEST_UPDATE_TAG)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "NAMESPACE_ID": TEST_NAMESPACE,
    }

    # Act
    cartography.intel.endorlabs.findings.sync_findings(
        neo4j_session,
        "fake-token",
        TEST_NAMESPACE,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: Finding nodes exist
    expected_nodes = {
        ("finding-001", "lodash-prototype-pollution", "FINDING_LEVEL_CRITICAL"),
        ("finding-002", "outdated-express-release", "FINDING_LEVEL_MEDIUM"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "EndorLabsFinding",
            ["id", "name", "level"],
        )
        == expected_nodes
    )

    # Assert: Also labeled as Risk
    assert (
        check_nodes(
            neo4j_session,
            "Risk",
            ["id", "name", "level"],
        )
        == expected_nodes
    )

    # Assert: Connected to projects via FOUND_IN
    expected_project_rels = {
        ("finding-001", "proj-001"),
        ("finding-002", "proj-001"),
    }
    assert (
        check_rels(
            neo4j_session,
            "EndorLabsFinding",
            "id",
            "EndorLabsProject",
            "id",
            "FOUND_IN",
            rel_direction_right=True,
        )
        == expected_project_rels
    )

    # Assert: CVE fields
    result = neo4j_session.run(
        "MATCH (f:EndorLabsFinding {id: 'finding-001'}) "
        "RETURN f.cve_id AS cve_id, f.summary AS summary, "
        "f.proposed_version AS proposed_version",
    ).single()
    assert result["cve_id"] == "CVE-2024-0001"
    assert result["summary"] == "Prototype pollution vulnerability in lodash"
    assert result["proposed_version"] == "4.17.22"

    # Assert: finding-002 has no CVE
    result = neo4j_session.run(
        "MATCH (f:EndorLabsFinding {id: 'finding-002'}) " "RETURN f.cve_id AS cve_id",
    ).single()
    assert result["cve_id"] is None
