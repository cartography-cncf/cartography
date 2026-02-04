"""
Integration tests for SBOM module.

The SBOM module creates DEPENDS_ON relationships between existing TrivyPackage nodes
(created by Trivy module) based on dependency graph from Syft CycloneDX SBOMs.

This enables tracing from CVE → transitive dep → direct dep → actionable fix.
"""

import json
from unittest.mock import mock_open
from unittest.mock import patch

from cartography.intel.sbom import sync_sbom_from_dir
from tests.data.sbom.cyclonedx_sample import CYCLONEDX_SBOM_SAMPLE
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _clear_test_data(neo4j_session):
    """Clear all test data to ensure test isolation."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _create_trivy_packages(neo4j_session, packages_data):
    """
    Helper to create TrivyPackage nodes simulating Trivy ingestion.

    TrivyPackage ID format: {version}|{name}
    """
    query = """
    UNWIND $packages AS pkg
    MERGE (p:Package:TrivyPackage {id: pkg.id})
    SET p.name = pkg.name,
        p.version = pkg.version,
        p.lastupdated = $update_tag
    """
    neo4j_session.run(query, packages=packages_data, update_tag=TEST_UPDATE_TAG)


def _create_trivy_findings(neo4j_session, findings_data):
    """
    Helper to create TrivyImageFinding nodes and AFFECTS relationships.
    """
    query = """
    UNWIND $findings AS finding
    MERGE (f:TrivyImageFinding {id: finding.id})
    SET f.cve_id = finding.cve_id,
        f.Severity = finding.severity,
        f.lastupdated = $update_tag
    WITH f, finding
    MATCH (p:TrivyPackage {id: finding.package_id})
    MERGE (f)-[:AFFECTS]->(p)
    """
    neo4j_session.run(query, findings=findings_data, update_tag=TEST_UPDATE_TAG)


def _setup_trivy_data_for_sbom_test(neo4j_session):
    """
    Set up TrivyPackage nodes and TrivyImageFinding nodes for SBOM tests.

    This simulates what the Trivy module would create before SBOM enrichment.
    """
    # Clear any existing data to ensure test isolation
    _clear_test_data(neo4j_session)

    # Create TrivyPackage nodes with Trivy ID format: {version}|{name}
    packages = [
        {"id": "4.17.1|express", "name": "express", "version": "4.17.1"},
        {"id": "4.17.20|lodash", "name": "lodash", "version": "4.17.20"},
        {"id": "1.3.7|accepts", "name": "accepts", "version": "1.3.7"},
        {"id": "2.1.27|mime-types", "name": "mime-types", "version": "2.1.27"},
        {"id": "1.19.0|body-parser", "name": "body-parser", "version": "1.19.0"},
    ]
    _create_trivy_packages(neo4j_session, packages)

    # Create TrivyImageFinding nodes and AFFECTS relationships
    findings = [
        {
            "id": "CVE-2021-23337",
            "cve_id": "CVE-2021-23337",
            "severity": "HIGH",
            "package_id": "4.17.20|lodash",
        },
        {
            "id": "CVE-2022-24999",
            "cve_id": "CVE-2022-24999",
            "severity": "HIGH",
            "package_id": "4.17.1|express",
        },
    ]
    _create_trivy_findings(neo4j_session, findings)


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(CYCLONEDX_SBOM_SAMPLE),
)
@patch(
    "cartography.intel.sbom.get_json_files_in_dir",
    return_value={"/tmp/sbom.json"},
)
def test_sync_sbom_creates_depends_on_relationships(
    mock_list_dir,
    mock_file_open,
    neo4j_session,
):
    """Test that SBOM sync creates DEPENDS_ON relationships between TrivyPackage nodes."""
    # Setup: Create TrivyPackage nodes (simulating Trivy ingestion)
    _setup_trivy_data_for_sbom_test(neo4j_session)

    # Act: Run SBOM sync
    sync_sbom_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert: Check DEPENDS_ON relationships
    depends_on_rels = check_rels(
        neo4j_session,
        "TrivyPackage",
        "name",
        "TrivyPackage",
        "name",
        "DEPENDS_ON",
        rel_direction_right=True,
    )

    # express depends on accepts and body-parser
    assert ("express", "accepts") in depends_on_rels
    assert ("express", "body-parser") in depends_on_rels

    # accepts depends on mime-types
    assert ("accepts", "mime-types") in depends_on_rels

    # We should have 3 DEPENDS_ON relationships total
    assert len(depends_on_rels) == 3


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(CYCLONEDX_SBOM_SAMPLE),
)
@patch(
    "cartography.intel.sbom.get_json_files_in_dir",
    return_value={"/tmp/sbom.json"},
)
def test_trace_cve_through_dependency_chain(
    mock_list_dir,
    mock_file_open,
    neo4j_session,
):
    """
    Test tracing a CVE through the dependency chain.

    This is the primary use case for the SBOM module: given a CVE on a transitive
    dependency, find which upstream packages depend on it.
    """
    # Setup: Create TrivyPackage nodes
    _setup_trivy_data_for_sbom_test(neo4j_session)

    # Add a CVE on a transitive dependency (accepts)
    neo4j_session.run(
        """
        MERGE (f:TrivyImageFinding {id: 'CVE-TRANSITIVE-001'})
        SET f.cve_id = 'CVE-TRANSITIVE-001',
            f.Severity = 'CRITICAL',
            f.lastupdated = $update_tag
        WITH f
        MATCH (p:TrivyPackage {id: '1.3.7|accepts'})
        MERGE (f)-[:AFFECTS]->(p)
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act: Run SBOM sync to add dependency graph
    sync_sbom_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Query: Find upstream package that depends on the vulnerable package
    result = neo4j_session.run(
        """
        MATCH (cve:TrivyImageFinding)-[:AFFECTS]->(vuln:TrivyPackage)
        WHERE cve.cve_id = 'CVE-TRANSITIVE-001'
        MATCH (upstream:TrivyPackage)-[:DEPENDS_ON]->(vuln)
        RETURN cve.cve_id AS cve_id,
               vuln.name AS vulnerable_package,
               upstream.name AS upstream_package
        """
    ).data()

    # Should find that express depends on accepts
    assert len(result) == 1
    assert result[0]["cve_id"] == "CVE-TRANSITIVE-001"
    assert result[0]["vulnerable_package"] == "accepts"
    assert result[0]["upstream_package"] == "express"


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(CYCLONEDX_SBOM_SAMPLE),
)
@patch(
    "cartography.intel.sbom.get_json_files_in_dir",
    return_value={"/tmp/sbom.json"},
)
def test_sbom_only_creates_relationships_for_existing_packages(
    mock_list_dir,
    mock_file_open,
    neo4j_session,
):
    """Test that SBOM sync only creates relationships for packages that exist."""
    # Clear data from previous tests to ensure isolation
    _clear_test_data(neo4j_session)

    # Setup: Create only some of the TrivyPackage nodes
    partial_packages = [
        {"id": "4.17.1|express", "name": "express", "version": "4.17.1"},
        {"id": "4.17.20|lodash", "name": "lodash", "version": "4.17.20"},
        # NOT creating: accepts, mime-types, body-parser
    ]
    _create_trivy_packages(neo4j_session, partial_packages)

    # Act: Run SBOM sync
    sync_sbom_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert: No DEPENDS_ON relationships should be created
    # (because accepts, body-parser don't exist as TrivyPackage nodes)
    result = neo4j_session.run(
        "MATCH (:TrivyPackage)-[r:DEPENDS_ON]->(:TrivyPackage) RETURN count(r) as count"
    ).single()
    assert result["count"] == 0

    # No new Package nodes should be created
    total_packages = neo4j_session.run(
        "MATCH (p:TrivyPackage) RETURN count(p) AS count"
    ).single()["count"]
    assert total_packages == 2


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(CYCLONEDX_SBOM_SAMPLE),
)
@patch(
    "cartography.intel.sbom.get_json_files_in_dir",
    return_value={"/tmp/sbom.json"},
)
def test_cleanup_removes_stale_depends_on_relationships(
    mock_list_dir,
    mock_file_open,
    neo4j_session,
):
    """Test that cleanup removes stale DEPENDS_ON relationships from previous sync."""
    # Setup: Create TrivyPackage nodes
    _setup_trivy_data_for_sbom_test(neo4j_session)

    # First sync
    sync_sbom_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Verify relationships exist
    result = neo4j_session.run(
        "MATCH (:TrivyPackage)-[r:DEPENDS_ON]->(:TrivyPackage) RETURN count(r) as count"
    ).single()
    assert result["count"] == 3

    # Second sync with new update tag
    NEW_UPDATE_TAG = TEST_UPDATE_TAG + 1000
    sync_sbom_from_dir(
        neo4j_session,
        "/tmp",
        NEW_UPDATE_TAG,
        {"UPDATE_TAG": NEW_UPDATE_TAG},
    )

    # Relationships should still exist with new update tag
    result = neo4j_session.run(
        "MATCH (:TrivyPackage)-[r:DEPENDS_ON]->(:TrivyPackage) WHERE r.lastupdated = $tag RETURN count(r) as count",
        tag=NEW_UPDATE_TAG,
    ).single()
    assert result["count"] == 3
