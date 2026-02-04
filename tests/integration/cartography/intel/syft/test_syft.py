"""
Integration tests for cartography.intel.syft module.

These tests verify that Syft ingestion correctly creates DEPENDS_ON
relationships between TrivyPackage nodes.
"""

import json
from unittest.mock import mock_open
from unittest.mock import patch

from cartography.intel.syft import sync_single_syft
from cartography.intel.syft import sync_syft_from_dir
from tests.data.syft.syft_sample import EXPECTED_DEPENDENCIES
from tests.data.syft.syft_sample import SYFT_SAMPLE
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _create_trivy_packages(neo4j_session, update_tag: int) -> None:
    """
    Create TrivyPackage nodes that would normally be created by Trivy sync.

    These packages match the artifacts in SYFT_SAMPLE so Syft can enrich them.
    Includes normalized_id for cross-tool matching with Syft.
    """
    # Packages from SYFT_SAMPLE: express, body-parser, bytes, accepts, lodash
    # normalized_id format: {type}|{normalized_name}|{version}
    packages = [
        {
            "id": "4.18.2|express",
            "name": "express",
            "version": "4.18.2",
            "normalized_id": "npm|express|4.18.2",
        },
        {
            "id": "1.20.1|body-parser",
            "name": "body-parser",
            "version": "1.20.1",
            "normalized_id": "npm|body-parser|1.20.1",
        },
        {
            "id": "3.1.2|bytes",
            "name": "bytes",
            "version": "3.1.2",
            "normalized_id": "npm|bytes|3.1.2",
        },
        {
            "id": "1.3.8|accepts",
            "name": "accepts",
            "version": "1.3.8",
            "normalized_id": "npm|accepts|1.3.8",
        },
        {
            "id": "4.17.21|lodash",
            "name": "lodash",
            "version": "4.17.21",
            "normalized_id": "npm|lodash|4.17.21",
        },
    ]

    for pkg in packages:
        neo4j_session.run(
            """
            MERGE (p:Package:TrivyPackage {id: $id})
            SET p.name = $name,
                p.version = $version,
                p.normalized_id = $normalized_id,
                p.lastupdated = $lastupdated
            """,
            id=pkg["id"],
            name=pkg["name"],
            version=pkg["version"],
            normalized_id=pkg["normalized_id"],
            lastupdated=update_tag,
        )


def test_sync_single_syft_creates_depends_on_relationships(neo4j_session):
    """
    Test that sync_single_syft creates DEPENDS_ON relationships between packages.
    """
    # Arrange: Create TrivyPackage nodes
    _create_trivy_packages(neo4j_session, TEST_UPDATE_TAG)

    # Act: Run Syft sync
    sync_single_syft(
        neo4j_session,
        SYFT_SAMPLE,
        TEST_UPDATE_TAG,
        sub_resource_label="SyftSync",
        sub_resource_id="test",
    )

    # Assert: Check DEPENDS_ON relationships were created
    # Uses normalized_id for matching (format: {type}|{normalized_name}|{version})
    actual_rels = check_rels(
        neo4j_session,
        "TrivyPackage",
        "normalized_id",
        "TrivyPackage",
        "normalized_id",
        "DEPENDS_ON",
        rel_direction_right=True,
    )

    assert actual_rels == EXPECTED_DEPENDENCIES


def test_sync_single_syft_no_packages_to_enrich(neo4j_session):
    """
    Test that sync_single_syft handles missing TrivyPackage nodes gracefully.

    This test uses different package names that don't exist in the database
    to verify the sync handles missing packages without errors.
    """
    # Count relationships before
    before_count = neo4j_session.run(
        """
        MATCH (:TrivyPackage)-[r:DEPENDS_ON]->(:TrivyPackage)
        RETURN count(r) AS count
        """
    ).single()["count"]

    # Use a Syft sample with packages that don't exist in the database
    non_matching_syft_data = {
        "artifacts": [
            {
                "id": "pkg:npm/nonexistent-pkg@1.0.0",
                "name": "nonexistent-pkg",
                "version": "1.0.0",
                "type": "npm",
            }
        ],
        "artifactRelationships": [],
    }

    # Act: Run Syft sync without any matching TrivyPackage nodes
    # This should not raise an error, just not create any relationships
    sync_single_syft(
        neo4j_session,
        non_matching_syft_data,
        TEST_UPDATE_TAG,
        sub_resource_label="SyftSync",
        sub_resource_id="test-no-packages",
    )

    # Assert: No new DEPENDS_ON relationships should have been created
    after_count = neo4j_session.run(
        """
        MATCH (:TrivyPackage)-[r:DEPENDS_ON]->(:TrivyPackage)
        RETURN count(r) AS count
        """
    ).single()["count"]

    assert after_count == before_count


def test_sync_single_syft_invalid_data(neo4j_session):
    """
    Test that sync_single_syft handles invalid Syft data gracefully.
    """
    # Count relationships before
    before_count = neo4j_session.run(
        """
        MATCH (:TrivyPackage)-[r:DEPENDS_ON]->(:TrivyPackage)
        RETURN count(r) AS count
        """
    ).single()["count"]

    # Act: Run Syft sync with invalid data (missing artifacts)
    invalid_data = {"source": {"type": "image"}}

    # Should not raise - just log an error and skip
    sync_single_syft(
        neo4j_session,
        invalid_data,
        TEST_UPDATE_TAG,
        sub_resource_label="SyftSync",
        sub_resource_id="test-invalid",
    )

    # Assert: No new relationships should have been created
    after_count = neo4j_session.run(
        """
        MATCH (:TrivyPackage)-[r:DEPENDS_ON]->(:TrivyPackage)
        RETURN count(r) AS count
        """
    ).single()["count"]

    assert after_count == before_count


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(SYFT_SAMPLE),
)
@patch(
    "cartography.intel.syft._get_json_files_in_dir",
    return_value={"/tmp/syft.json"},
)
def test_sync_syft_from_dir(
    mock_list_dir_scan_results,
    mock_file_open,
    neo4j_session,
):
    """
    Test sync_syft_from_dir reads files and creates DEPENDS_ON relationships.
    """
    # Arrange: Create TrivyPackage nodes
    _create_trivy_packages(neo4j_session, TEST_UPDATE_TAG)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "_sub_resource_label": "SyftSync",
        "_sub_resource_id": "test",
    }

    # Act: Sync from directory
    sync_syft_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: DEPENDS_ON relationships should exist
    result = neo4j_session.run(
        """
        MATCH (:TrivyPackage)-[r:DEPENDS_ON]->(:TrivyPackage)
        RETURN count(r) AS count
        """
    ).single()

    assert result["count"] == 3  # 3 relationships in SYFT_SAMPLE


def test_depends_on_relationship_properties(neo4j_session):
    """
    Test that DEPENDS_ON relationships have the correct properties.
    """
    # Arrange
    _create_trivy_packages(neo4j_session, TEST_UPDATE_TAG)

    # Act
    sync_single_syft(
        neo4j_session,
        SYFT_SAMPLE,
        TEST_UPDATE_TAG,
        sub_resource_label="SyftSync",
        sub_resource_id="test-id",
    )

    # Assert: Check relationship properties
    result = neo4j_session.run(
        """
        MATCH (:TrivyPackage)-[r:DEPENDS_ON]->(:TrivyPackage)
        RETURN r.lastupdated AS lastupdated,
               r._sub_resource_label AS sub_label,
               r._sub_resource_id AS sub_id
        LIMIT 1
        """
    ).single()

    assert result["lastupdated"] == TEST_UPDATE_TAG
    assert result["sub_label"] == "SyftSync"
    assert result["sub_id"] == "test-id"


def test_transitive_cve_tracing_query(neo4j_session):
    """
    Test the key query for tracing CVEs through transitive dependencies.

    This verifies the use case:
    CVE affects transitive dep -> trace to direct dep -> "update this package"

    Direct vs transitive is determined by graph structure:
    - Direct deps: packages with no incoming DEPENDS_ON edges
    - Transitive deps: packages that have incoming DEPENDS_ON edges
    """
    # Arrange: Create packages and a mock CVE finding
    _create_trivy_packages(neo4j_session, TEST_UPDATE_TAG)

    # Create a finding that affects the transitive "bytes" package
    neo4j_session.run(
        """
        MERGE (f:TrivyImageFinding {id: 'TIF|CVE-2023-12345'})
        SET f.cve_id = 'CVE-2023-12345',
            f.severity = 'HIGH',
            f.lastupdated = $lastupdated
        WITH f
        MATCH (p:TrivyPackage {id: '3.1.2|bytes'})
        MERGE (f)-[:AFFECTS]->(p)
        """,
        lastupdated=TEST_UPDATE_TAG,
    )

    # Run Syft sync to create dependencies
    sync_single_syft(
        neo4j_session,
        SYFT_SAMPLE,
        TEST_UPDATE_TAG,
        sub_resource_label="SyftSync",
        sub_resource_id="test",
    )

    # Act: Run the transitive CVE tracing query using graph patterns
    # Direct deps = packages with no incoming DEPENDS_ON edges (nothing depends on them)
    # Transitive deps = packages that have incoming DEPENDS_ON edges
    result = neo4j_session.run(
        """
        MATCH (cve:TrivyImageFinding)-[:AFFECTS]->(vuln:TrivyPackage)
        WHERE exists((vuln)<-[:DEPENDS_ON]-())
        MATCH (direct:TrivyPackage)-[:DEPENDS_ON*1..5]->(vuln)
        WHERE NOT exists((direct)<-[:DEPENDS_ON]-())
        RETURN cve.cve_id AS cve_id,
               vuln.name AS vulnerable_package,
               direct.name AS direct_dependency
        """
    ).data()

    # Assert: Should find that CVE-2023-12345 affects bytes,
    # and express and lodash are direct (nothing depends on them):
    # - express -> body-parser -> bytes
    # - lodash has no dependencies
    # Only express leads to bytes through the chain
    assert len(result) == 1
    assert result[0]["cve_id"] == "CVE-2023-12345"
    assert result[0]["vulnerable_package"] == "bytes"
    assert result[0]["direct_dependency"] == "express"
