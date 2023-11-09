from string import Template
from typing import List
from unittest.mock import patch

import neo4j

import cartography.intel.semgrep.findings
import tests.data.semgrep.sca
from cartography.intel.semgrep.findings import sync
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_REPO_ID = "https://github.com/yourorg/yourrepo"
TEST_REPO_FULL_NAME = "yourorg/yourrepo"
TEST_REPO_NAME = "yourrepo"
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
        dep_id="grav|1.7.42.0",
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
        cve_id="CVE-2023-37897",
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
    ) == {("123456", "YourOrg", "yourorg")}

    assert _check_nodes_as_list(
        neo4j_session,
        "SemgrepSCAFinding",
        [
            "id",
            "lastupdated",
            "repository",
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
        "132465::::ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590::reachable",
        TEST_UPDATE_TAG,
        "yourorg/yourrepo",
        "ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590",
        "Reachable vuln",
        "description",
        "go",
        "HIGH",
        "CVE-2023-37897",
        "MANUAL_REVIEW_REACHABLE",
        "REACHABLE",
        "DIRECT",
        "grav|1.7.42.0",
        "grav|1.7.42.2",
        "go.mod",
        "https://github.com/yourorg/yourrepo/blame/71bbed12f950de8335006d7f91112263d8504f1b/go.mod#L111",
        [
            "https://github.com/advisories//GHSA-9436-3gmp-4f53",
            "https://nvd.nist.gov/vuln/detail/CVE-2023-37897",
        ],
        "2023-07-19T12:51:53Z",
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
            "20128504",
            "src/packages/directory/file1.go",
            "24",
            "57",
            "24",
            "78",
            "https://github.com/yourorg/yourrepo/blame/6fdee8f2727f4506cfbbe553e23b895e27956588/src/packages/directory/file1.go.ts#L24",  # noqa E501
        ),
        (
            "20128505",
            "src/packages/directory/file2.go",
            "24",
            "37",
            "24",
            "54",
            "https://github.com/yourorg/yourrepo/blame/6fdee8f2727f4506cfbbe553e23b895e27956588/src/packages/directory/file2.go.ts#L24",  # noqa E501
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
            "132465::::ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590::reachable",
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
            "20128504",
        ),
        (
            "123456",
            "20128505",
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
            "yourorg/yourrepo",
            "132465::::ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590::reachable",
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
            "132465::::ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590::reachable",
            "20128504",
        ),
        (
            "132465::::ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590::reachable",
            "20128505",
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
            "132465::::ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590::reachable",
            "grav|1.7.42.0",
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
            "CVE-2023-37897",
            "132465::::ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590::reachable",
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
            "132465::::ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590::reachable",
            "REACHABLE",
            "MANUAL_REVIEW_REACHABLE",
            "HIGH",
            "MEDIUM",
        ),
    }
