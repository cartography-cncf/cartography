"""
Integration tests for cartography.intel.syft module.

These tests verify that Syft ingestion correctly creates SyftPackage nodes
with DEPENDS_ON relationships between them.
"""

import json
from unittest.mock import mock_open
from unittest.mock import patch

from cartography.intel.syft import sync_single_syft
from cartography.intel.syft import sync_syft_from_dir
from tests.data.syft.syft_sample import EXPECTED_SYFT_PACKAGE_DEPENDENCIES
from tests.data.syft.syft_sample import EXPECTED_SYFT_PACKAGES
from tests.data.syft.syft_sample import SYFT_SAMPLE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def test_sync_single_syft_creates_syft_package_nodes(neo4j_session):
    """
    Test that sync_single_syft creates SyftPackage nodes with correct properties.
    """
    neo4j_session.run("MATCH (n:SyftPackage) DETACH DELETE n")

    sync_single_syft(
        neo4j_session,
        SYFT_SAMPLE,
        TEST_UPDATE_TAG,
    )

    # Check SyftPackage nodes exist with expected IDs
    actual_nodes = check_nodes(neo4j_session, "SyftPackage", ["id"])
    expected_nodes = {(pkg_id,) for pkg_id in EXPECTED_SYFT_PACKAGES}
    assert actual_nodes == expected_nodes

    # Verify a specific node has all expected properties
    result = neo4j_session.run(
        """
        MATCH (p:SyftPackage {id: 'npm|express|4.18.2'})
        RETURN p.name AS name, p.version AS version, p.type AS type,
               p.purl AS purl, p.language AS language, p.found_by AS found_by,
               p.normalized_id AS normalized_id, p.lastupdated AS lastupdated
        """,
    ).single()

    assert result["name"] == "express"
    assert result["version"] == "4.18.2"
    assert result["type"] == "npm"
    assert result["purl"] == "pkg:npm/express@4.18.2"
    assert result["language"] == "javascript"
    assert result["found_by"] == "javascript-package-cataloger"
    assert result["normalized_id"] == "npm|express|4.18.2"
    assert result["lastupdated"] == TEST_UPDATE_TAG


def test_sync_single_syft_creates_depends_on(neo4j_session):
    """
    Test that sync_single_syft creates DEPENDS_ON between SyftPackage nodes.
    """
    sync_single_syft(
        neo4j_session,
        SYFT_SAMPLE,
        TEST_UPDATE_TAG,
    )

    actual_rels = check_rels(
        neo4j_session,
        "SyftPackage",
        "id",
        "SyftPackage",
        "id",
        "DEPENDS_ON",
        rel_direction_right=True,
    )

    assert actual_rels == EXPECTED_SYFT_PACKAGE_DEPENDENCIES


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
    Test sync_syft_from_dir reads files and creates SyftPackage nodes.
    """
    neo4j_session.run("MATCH (n:SyftPackage) DETACH DELETE n")

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    sync_syft_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: SyftPackage nodes should exist
    actual_nodes = check_nodes(neo4j_session, "SyftPackage", ["id"])
    assert len(actual_nodes) == 5

    # Assert: DEPENDS_ON relationships should exist
    result = neo4j_session.run(
        """
        MATCH (:SyftPackage)-[r:DEPENDS_ON]->(:SyftPackage)
        RETURN count(r) AS count
        """
    ).single()

    assert result["count"] == 3
