from string import Template
from typing import List
from unittest.mock import patch

import neo4j

import cartography.intel.semgrep.findings
import tests.data.semgrep.sca
from cartography.intel.semgrep.findings import sync
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_REPO_ID = "https: //github.com/org/repository"
TEST_REPO_FULL_NAME = "org/repository"
TEST_REPO_NAME = "repository"
TEST_UPDATE_TAG = 123456789


def _check_nodes_as_list(
    neo4j_session: neo4j.Session, node_label: str, attrs: List[str],
):
    """
    Like tests.integration.util.check_nodes()` but returns a list instead of a set.
    """
    if not attrs:
        raise ValueError(
            "`attrs` passed to check_nodes() must have at least one element.",
        )

    attrs = ", ".join(f"n.{attr}" for attr in attrs)
    query_template = Template("MATCH (n:$NodeLabel) RETURN $Attrs")
    result = neo4j_session.run(
        query_template.safe_substitute(NodeLabel=node_label, Attrs=attrs),
    )
    return sum([row.values() for row in result], [])


def _create_github_repos(neo4j_session):
    # Creates a set of GitHub repositories in the graph
    neo4j_session.run(
        """
        MERGE (repo:GitHubRepository{id: $repo_id, fullname: $repo_fullname, name: $repo_name})
        ON CREATE SET repo.firstseen = timestamp()
        SET repo.lastupdated = $update_tag
        SET repo.archived = false
        """,
        repo_id=TEST_REPO_ID,
        repo_fullname=TEST_REPO_FULL_NAME,
        update_tag=TEST_UPDATE_TAG,
        repo_name=TEST_REPO_NAME,
    )


def _create_dependency_nodes(neo4j_session):
    # Creates a set of dependency nodes in the graph
    neo4j_session.run(
        """
        MERGE (dep:Dependency{id: $dep_id})
        ON CREATE SET dep.firstseen = timestamp()
        SET dep.lastupdated = $update_tag
        """,
        dep_id="moment|2.29.2",
        update_tag=TEST_UPDATE_TAG,
    )


def _create_cve_nodes(neo4j_session):
    # Creates a set of CVE nodes in the graph
    neo4j_session.run(
        """
        MERGE (cve:CVE{id: $cve_id})
        ON CREATE SET cve.firstseen = timestamp()
        SET cve.lastupdated = $update_tag
        """,
        cve_id="CVE-2022-31129",
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.semgrep.findings,
    "get_deployment",
    return_value=tests.data.semgrep.sca.DEPLOYMENTS,
)
@patch.object(
    cartography.intel.semgrep.findings,
    "get_sca_vulns",
    return_value=tests.data.semgrep.sca.RAW_VULNS,
)
def test_sync(mock_get_sca_vulns, mock_get_deployment, neo4j_session):
    # Arrange
    _create_github_repos(neo4j_session)
    _create_dependency_nodes(neo4j_session)
    _create_cve_nodes(neo4j_session)
    semgrep_app_token = "your_semgrep_app_token"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    sync(neo4j_session, semgrep_app_token, TEST_UPDATE_TAG, common_job_parameters)

    # Assert

    assert check_nodes(
        neo4j_session,
        "SemgrepDeployment",
        ["id", "name", "slug"],
    ) == {("123456", "Org", "org")}

    assert _check_nodes_as_list(
        neo4j_session,
        "SemgrepSCAFinding",
        [
            "id",
            "lastupdated",
            "repository",
            "branch",
            "rule_id",
            "summary",
            "description",
            "package_manager",
            "severity",
            "cve_id",
            "reachability_check",
            "reachability",
            "transitivity",
            "dependency",
            "dependency_fix",
            "dependency_file",
            "dependency_file_url",
            "ref_urls",
            "scan_time",
        ],
    ) == [
        tests.data.semgrep.sca.VULN_ID,
        TEST_UPDATE_TAG,
        "org/repository",
        "main",
        "ssc-1e99e462-0fc5-4109-ad52-d2b5a7048232",
        "moment:Denial-of-Service (DoS)",
        "description",
        "npm",
        "HIGH",
        "CVE-2022-31129",
        "REACHABLE",
        "REACHABLE",
        "DIRECT",
        "moment|2.29.2",
        "moment|2.29.4",
        "package-lock.json",
        "https: //github.com/org/repository/blob/commit_id/package-lock.json#L14373",
        [
            "https://nvd.nist.gov/vuln/detail/CVE-2022-31129",
        ],
        "2024-07-11T20:46:25.269650Z",
    ]

    assert check_nodes(
        neo4j_session,
        "SemgrepSCALocation",
        [
            "id",
            "path",
            "start_line",
            "start_col",
            "end_line",
            "end_col",
            "url",
        ],
    ) == {
        (
            tests.data.semgrep.sca.USAGE_ID,
            "src/packages/linked-accounts/components/LinkedAccountsTable/constants.tsx",
            274,
            37,
            274,
            62,
            "https: //github.com/org/repository/blob/commit_id/src/packages/linked-accounts/components/LinkedAccountsTable/constants.tsx#L274",  # noqa E501
        ),
    }

    assert check_rels(
        neo4j_session,
        "SemgrepDeployment",
        "id",
        "SemgrepSCAFinding",
        "id",
        "RESOURCE",
    ) == {
        (
            "123456",
            tests.data.semgrep.sca.VULN_ID,
        ),
    }

    assert check_rels(
        neo4j_session,
        "SemgrepDeployment",
        "id",
        "SemgrepSCALocation",
        "id",
        "RESOURCE",
    ) == {
        (
            "123456",
            tests.data.semgrep.sca.USAGE_ID,
        ),
    }

    assert check_rels(
        neo4j_session,
        "GitHubRepository",
        "fullname",
        "SemgrepSCAFinding",
        "id",
        "FOUND_IN",
        rel_direction_right=False,
    ) == {
        (
            "org/repository",
            tests.data.semgrep.sca.VULN_ID,
        ),
    }

    assert check_rels(
        neo4j_session,
        "SemgrepSCAFinding",
        "id",
        "SemgrepSCALocation",
        "id",
        "USAGE_AT",
    ) == {
        (
            tests.data.semgrep.sca.VULN_ID,
            tests.data.semgrep.sca.USAGE_ID,
        ),
    }

    assert check_rels(
        neo4j_session,
        "SemgrepSCAFinding",
        "id",
        "Dependency",
        "id",
        "AFFECTS",
    ) == {
        (
            tests.data.semgrep.sca.VULN_ID,
            "moment|2.29.2",
        ),
    }

    assert check_rels(
        neo4j_session,
        "CVE",
        "id",
        "SemgrepSCAFinding",
        "id",
        "LINKED_TO",
    ) == {
        (
            "CVE-2022-31129",
            tests.data.semgrep.sca.VULN_ID,
        ),
    }

    assert check_nodes(
        neo4j_session,
        "SemgrepSCAFinding",
        [
            "id",
            "reachability",
            "reachability_check",
            "severity",
            "reachability_risk",
        ],
    ) == {
        (
            tests.data.semgrep.sca.VULN_ID,
            "REACHABLE",
            "REACHABLE",
            "HIGH",
            "HIGH",
        ),
    }
