import json
from pathlib import Path
from unittest.mock import patch

import cartography.intel.semgrep.deployment
import cartography.intel.semgrep.findings
import tests.data.semgrep.deployment
import tests.data.semgrep.sast
import tests.data.semgrep.sca
from cartography.intel.semgrep.deployment import sync_deployment
from cartography.intel.semgrep.findings import sync_findings
from cartography.intel.semgrep.ossfindings import OSS_DEPLOYMENT_ID
from cartography.intel.semgrep.ossfindings import sync_oss_semgrep_sast_findings
from tests.integration.cartography.intel.semgrep.common import check_nodes_as_list
from tests.integration.cartography.intel.semgrep.common import create_cve_nodes
from tests.integration.cartography.intel.semgrep.common import create_dependency_nodes
from tests.integration.cartography.intel.semgrep.common import create_github_repos
from tests.integration.cartography.intel.semgrep.common import TEST_REPO_ID
from tests.integration.cartography.intel.semgrep.common import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


@patch.object(
    cartography.intel.semgrep.deployment,
    "get_deployment",
    return_value=tests.data.semgrep.deployment.DEPLOYMENTS,
)
@patch.object(
    cartography.intel.semgrep.findings,
    "get_sast_findings",
    return_value=tests.data.semgrep.sast.RAW_FINDINGS,
)
def test_sync_sast_findings(mock_get_sast_findings, mock_get_deployment, neo4j_session):
    # Arrange
    create_github_repos(neo4j_session)
    semgrep_app_token = "your_semgrep_app_token"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    sync_deployment(
        neo4j_session,
        semgrep_app_token,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    with patch.object(
        cartography.intel.semgrep.findings,
        "get_sca_vulns",
        return_value=[],
    ):
        sync_findings(
            neo4j_session,
            semgrep_app_token,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

    # Assert nodes
    assert check_nodes(
        neo4j_session,
        "SemgrepSASTFinding",
        [
            "id",
            "rule_id",
            "repository",
            "repository_url",
            "branch",
            "severity",
            "confidence",
            "triage_status",
            "fix_status",
        ],
    ) == {
        (
            tests.data.semgrep.sast.SAST_FINDING_ID,
            "python.lang.security.audit.sqli.formatted-sql-query",
            "simpsoncorp/sample_repo",
            "https://github.com/simpsoncorp/sample_repo",
            "main",
            "HIGH",
            "HIGH",
            "untriaged",
            "open",
        ),
    }

    assert check_nodes(
        neo4j_session,
        "SemgrepSASTFinding",
        ["id", "file_path", "start_line", "start_col", "end_line", "end_col"],
    ) == {
        (
            tests.data.semgrep.sast.SAST_FINDING_ID,
            "src/api/auth.py",
            42,
            10,
            42,
            65,
        ),
    }

    # Assert deployment relationship
    assert check_rels(
        neo4j_session,
        "SemgrepDeployment",
        "id",
        "SemgrepSASTFinding",
        "id",
        "RESOURCE",
    ) == {
        (
            "123456",
            tests.data.semgrep.sast.SAST_FINDING_ID,
        ),
    }

    # Assert GitHub repo relationship
    assert check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "SemgrepSASTFinding",
        "id",
        "FOUND_IN",
        rel_direction_right=False,
    ) == {
        (
            "https://github.com/simpsoncorp/sample_repo",
            tests.data.semgrep.sast.SAST_FINDING_ID,
        ),
    }

    expected_assistant_id = (
        f"semgrep-assistant-{tests.data.semgrep.sast.SAST_FINDING_ID}"
    )

    # Assert assistant node
    assert check_nodes(
        neo4j_session,
        "SemgrepFindingAssistant",
        [
            "id",
            "autotriage_verdict",
            "autotriage_reason",
            "component_tag",
            "component_risk",
            "guidance_summary",
            "rule_explanation_summary",
        ],
    ) == {
        (
            expected_assistant_id,
            "true_positive",
            "",
            "user data",
            "high",
            "Use parameterized queries instead of string concatenation.",
            "User input directly concatenated into SQL query",
        ),
    }

    # Assert HAS_ASSISTANT relationship
    assert check_rels(
        neo4j_session,
        "SemgrepSASTFinding",
        "id",
        "SemgrepFindingAssistant",
        "id",
        "HAS_ASSISTANT",
    ) == {
        (
            tests.data.semgrep.sast.SAST_FINDING_ID,
            expected_assistant_id,
        ),
    }


@patch.object(
    cartography.intel.semgrep.deployment,
    "get_deployment",
    return_value=tests.data.semgrep.deployment.DEPLOYMENTS,
)
@patch.object(
    cartography.intel.semgrep.findings,
    "get_sast_findings",
    return_value=[],
)
@patch.object(
    cartography.intel.semgrep.findings,
    "get_sca_vulns",
    return_value=tests.data.semgrep.sca.RAW_VULNS,
)
def test_sync_findings(
    mock_get_sca_vulns, mock_get_sast_findings, mock_get_deployment, neo4j_session
):
    # Arrange
    create_github_repos(neo4j_session)
    create_dependency_nodes(neo4j_session)
    create_cve_nodes(neo4j_session)
    semgrep_app_token = "your_semgrep_app_token"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    sync_deployment(
        neo4j_session,
        semgrep_app_token,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    sync_findings(
        neo4j_session,
        semgrep_app_token,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "SemgrepDeployment",
        ["id", "name", "slug"],
    ) == {("123456", "Org", "org")}

    assert check_nodes_as_list(
        neo4j_session,
        "SemgrepSCAFinding",
        [
            "id",
            "lastupdated",
            "repository",
            "repository_url",
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
        order_by="id",
    ) == [
        tests.data.semgrep.sca.VULN_ID,
        TEST_UPDATE_TAG,
        "simpsoncorp/sample_repo",
        "https://github.com/simpsoncorp/sample_repo",
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
        "https: //github.com/simpsoncorp/sample_repo/blob/commit_id/package-lock.json#L14373",
        [
            "https://nvd.nist.gov/vuln/detail/CVE-2022-31129",
        ],
        "2024-07-11T20:46:25.269650Z",
        tests.data.semgrep.sca.VULN_ID_UNKNOWN,
        TEST_UPDATE_TAG,
        "simpsoncorp/sample_repo",
        "https://github.com/simpsoncorp/sample_repo",
        "main",
        "ssc-1e99e462-0fc5-4109-ad52-d2b5a7048232",
        "moment:Denial-of-Service (DoS)",
        "description",
        "npm",
        "HIGH",
        "UNKNOWN-2022-31129",
        "UNREACHABLE",
        "UNREACHABLE",
        "DIRECT",
        "moment|2.29.2",
        "moment|2.29.4",
        "package-lock.json",
        "https: //github.com/simpsoncorp/sample_repo/blob/commit_id/package-lock.json#L14373",
        [],
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
            "https: //github.com/simpsoncorp/sample_repo/blob/commit_id/src/packages/linked-accounts/components/LinkedAccountsTable/constants.tsx#L274",  # noqa E501
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
        (
            "123456",
            tests.data.semgrep.sca.VULN_ID_UNKNOWN,
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
        "id",
        "SemgrepSCAFinding",
        "id",
        "FOUND_IN",
        rel_direction_right=False,
    ) == {
        (
            "https://github.com/simpsoncorp/sample_repo",
            tests.data.semgrep.sca.VULN_ID,
        ),
        (
            "https://github.com/simpsoncorp/sample_repo",
            tests.data.semgrep.sca.VULN_ID_UNKNOWN,
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
        (
            tests.data.semgrep.sca.VULN_ID_UNKNOWN,
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
        (
            tests.data.semgrep.sca.VULN_ID_UNKNOWN,
            "UNREACHABLE",
            "UNREACHABLE",
            "HIGH",
            "INFO",
        ),
    }


def test_sync_oss_sast_findings(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_github_repos(neo4j_session)

    report_fixture_path = Path("tests/data/semgrep/oss_sast_report.json")
    report_document = json.loads(report_fixture_path.read_text())
    expected_finding_nodes = set()
    expected_resource_rels = set()
    expected_found_in_rels = set()

    for result in report_document["results"]:
        expected_finding_nodes.add((result["check_id"],))
        expected_resource_rels.add((OSS_DEPLOYMENT_ID, result["check_id"]))
        expected_found_in_rels.add((TEST_REPO_ID, result["check_id"]))

    sync_oss_semgrep_sast_findings(
        neo4j_session,
        "tests/data/semgrep/repository_mappings_single_repo.yaml",
        TEST_UPDATE_TAG,
    )

    assert check_nodes(
        neo4j_session,
        "SemgrepDeployment",
        ["id"],
    ) == {(OSS_DEPLOYMENT_ID,)}

    assert (
        check_nodes(
            neo4j_session,
            "SemgrepSASTFinding",
            ["rule_id"],
        )
        == expected_finding_nodes
    )

    assert (
        check_rels(
            neo4j_session,
            "SemgrepDeployment",
            "id",
            "SemgrepSASTFinding",
            "rule_id",
            "RESOURCE",
        )
        == expected_resource_rels
    )

    assert (
        check_rels(
            neo4j_session,
            "GitHubRepository",
            "id",
            "SemgrepSASTFinding",
            "rule_id",
            "FOUND_IN",
            rel_direction_right=False,
        )
        == expected_found_in_rels
    )


def test_sync_oss_sast_findings_multi_entry_multi_report(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_github_repos(neo4j_session)
    # Seed the second GitHubRepository node so FOUND_IN can match the second
    # repository mapping entry during OSS sync.
    neo4j_session.run(
        """
        MERGE (repo:GitHubRepository{id: $repo_id, fullname: $repo_fullname, name: $repo_name})
        ON CREATE SET repo.firstseen = timestamp()
        SET repo.lastupdated = $update_tag
        SET repo.archived = false
        """,
        repo_id="https://github.com/simpsoncorp/sample_repo_two",
        repo_fullname="simpsoncorp/sample_repo_two",
        repo_name="sample_repo_two",
        update_tag=TEST_UPDATE_TAG,
    )

    report_to_repo = {
        "tests/data/semgrep/oss_sast_report_2.json": TEST_REPO_ID,
        "tests/data/semgrep/oss_sast_report_3.json": "https://github.com/simpsoncorp/sample_repo_two",
        "tests/data/semgrep/oss_sast_report_4.json": "https://github.com/simpsoncorp/sample_repo_two",
    }
    expected_finding_nodes = set()
    expected_resource_rels = set()
    expected_found_in_rels = set()

    for report_path, repository_id in report_to_repo.items():
        report_document = json.loads(Path(report_path).read_text())
        for result in report_document["results"]:
            expected_finding_nodes.add((result["check_id"],))
            expected_resource_rels.add((OSS_DEPLOYMENT_ID, result["check_id"]))
            expected_found_in_rels.add((repository_id, result["check_id"]))

    sync_oss_semgrep_sast_findings(
        neo4j_session,
        "tests/data/semgrep/repository_mappings_multi_entry.yaml",
        TEST_UPDATE_TAG,
    )

    assert check_nodes(
        neo4j_session,
        "SemgrepDeployment",
        ["id"],
    ) == {(OSS_DEPLOYMENT_ID,)}

    assert (
        check_nodes(
            neo4j_session,
            "SemgrepSASTFinding",
            ["rule_id"],
        )
        == expected_finding_nodes
    )

    assert (
        check_rels(
            neo4j_session,
            "SemgrepDeployment",
            "id",
            "SemgrepSASTFinding",
            "rule_id",
            "RESOURCE",
        )
        == expected_resource_rels
    )

    assert (
        check_rels(
            neo4j_session,
            "GitHubRepository",
            "id",
            "SemgrepSASTFinding",
            "rule_id",
            "FOUND_IN",
            rel_direction_right=False,
        )
        == expected_found_in_rels
    )


def test_sync_oss_sast_findings_partial_failure_preserves_stale_repo(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_github_repos(neo4j_session)
    # Seed the second GitHubRepository node so FOUND_IN can match the second
    # repository mapping entry during OSS sync.
    neo4j_session.run(
        """
        MERGE (repo:GitHubRepository{id: $repo_id, fullname: $repo_fullname, name: $repo_name})
        ON CREATE SET repo.firstseen = timestamp()
        SET repo.lastupdated = $update_tag
        SET repo.archived = false
        """,
        repo_id="https://github.com/simpsoncorp/sample_repo_two",
        repo_fullname="simpsoncorp/sample_repo_two",
        repo_name="sample_repo_two",
        update_tag=TEST_UPDATE_TAG,
    )
    # Seed one stale OSS finding per repo under the synthetic deployment so the
    # sync can prove repo-scoped cleanup behavior: repo A should be deleted
    # after a fully successful snapshot, while repo B should be preserved when
    # one of its listed report artifacts fails.
    neo4j_session.run(
        """
        MERGE (deployment:SemgrepDeployment {id: $deployment_id})
        ON CREATE SET deployment.firstseen = timestamp()
        SET deployment.lastupdated = $stale_update_tag,
            deployment.name = "OSS Semgrep",
            deployment.slug = "oss"

        MERGE (repo_a_finding:SemgrepSASTFinding {id: "stale-a"})
        ON CREATE SET repo_a_finding.firstseen = timestamp()
        SET repo_a_finding.lastupdated = $stale_update_tag,
            repo_a_finding.rule_id = "stale-rule-a",
            repo_a_finding.repository = "simpsoncorp/sample_repo",
            repo_a_finding.repository_url = $repo_a_url,
            repo_a_finding.branch = "main"

        MERGE (repo_b_finding:SemgrepSASTFinding {id: "stale-b"})
        ON CREATE SET repo_b_finding.firstseen = timestamp()
        SET repo_b_finding.lastupdated = $stale_update_tag,
            repo_b_finding.rule_id = "stale-rule-b",
            repo_b_finding.repository = "simpsoncorp/sample_repo_two",
            repo_b_finding.repository_url = $repo_b_url,
            repo_b_finding.branch = "main"

        MERGE (deployment)-[:RESOURCE]->(repo_a_finding)
        MERGE (deployment)-[:RESOURCE]->(repo_b_finding)
        WITH repo_a_finding, repo_b_finding
        MATCH (repo_a:GitHubRepository {id: $repo_a_url})
        MATCH (repo_b:GitHubRepository {id: $repo_b_url})
        MERGE (repo_a_finding)-[:FOUND_IN]->(repo_a)
        MERGE (repo_b_finding)-[:FOUND_IN]->(repo_b)
        """,
        deployment_id=OSS_DEPLOYMENT_ID,
        stale_update_tag=TEST_UPDATE_TAG - 1,
        repo_a_url=TEST_REPO_ID,
        repo_b_url="https://github.com/simpsoncorp/sample_repo_two",
    )

    sync_oss_semgrep_sast_findings(
        neo4j_session,
        "tests/data/semgrep/repository_mappings_partial_failure.yaml",
        TEST_UPDATE_TAG,
    )

    finding_rule_ids = check_nodes(
        neo4j_session,
        "SemgrepSASTFinding",
        ["rule_id"],
    )
    assert ("stale-rule-a",) not in finding_rule_ids
    assert ("stale-rule-b",) in finding_rule_ids

    found_in_rels = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "SemgrepSASTFinding",
        "rule_id",
        "FOUND_IN",
        rel_direction_right=False,
    )
    assert (TEST_REPO_ID, "stale-rule-a") not in found_in_rels
    assert (
        "https://github.com/simpsoncorp/sample_repo_two",
        "stale-rule-b",
    ) in found_in_rels
