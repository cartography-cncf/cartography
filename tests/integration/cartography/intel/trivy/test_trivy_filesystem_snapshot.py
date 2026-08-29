import json

import cartography.intel.trivy
from cartography.intel.common.object_store import ListedReportReader
from cartography.intel.common.object_store import ReportRef
from cartography.intel.trivy.scanner import cleanup_filesystem_snapshot_relationships
from cartography.intel.trivy.scanner import cleanup_image_relationships
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
SNAPSHOT_IDS = ["railway-deployment-1", "railway-deployment-2"]
SOURCE_REVISION = "0123456789abcdef0123456789abcdef01234567"


def test_sync_trivy_repository_report_to_filesystem_snapshot(neo4j_session):
    # Arrange
    neo4j_session.run(
        """
        UNWIND $ids AS id
        MERGE (snapshot:RailwayFilesystemSnapshot:FilesystemSnapshot {id: id})
        SET snapshot.source_repo = "acme/api",
            snapshot.source_revision = $revision,
            snapshot.lastupdated = $update_tag
        """,
        ids=SNAPSHOT_IDS,
        revision=SOURCE_REVISION,
        update_tag=TEST_UPDATE_TAG,
    )
    payload = {
        "SchemaVersion": 2,
        "ArtifactName": "/tmp/api",
        "ArtifactType": "repository",
        "Metadata": {
            "RepoURL": "git@github.com:acme/api.git",
            "Commit": SOURCE_REVISION.upper(),
        },
        "Results": [
            {
                "Target": "requirements.txt",
                "Class": "lang-pkgs",
                "Type": "pip",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2026-12345",
                        "PkgName": "example-package",
                        "InstalledVersion": "1.0.0",
                        "FixedVersion": "1.0.1",
                        "Severity": "HIGH",
                    },
                ],
            },
        ],
    }
    ref = ReportRef(uri="memory://filesystem.json", name="filesystem.json")
    reader = ListedReportReader(
        "memory://trivy-reports",
        [ref],
        lambda _ref: json.dumps(payload).encode(),
    )

    # Act
    cartography.intel.trivy.sync_trivy_from_report_reader(
        neo4j_session,
        reader,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "TrivyImageFinding",
        "id",
        "FilesystemSnapshot",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("TIF|CVE-2026-12345", SNAPSHOT_IDS[0]),
        ("TIF|CVE-2026-12345", SNAPSHOT_IDS[1]),
    }
    assert check_rels(
        neo4j_session,
        "TrivyPackage",
        "id",
        "FilesystemSnapshot",
        "id",
        "DEPLOYED",
        rel_direction_right=True,
    ) == {
        ("1.0.0|example-package", SNAPSHOT_IDS[0]),
        ("1.0.0|example-package", SNAPSHOT_IDS[1]),
    }


def test_filesystem_cleanup_preserves_image_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (snapshot:FilesystemSnapshot {id: "cleanup-snapshot"})
        MERGE (image:Image {id: "cleanup-image"})
        MERGE (finding:TrivyImageFinding {id: "cleanup-finding"})
        MERGE (package:TrivyPackage {id: "cleanup-package"})
        MERGE (finding)-[:AFFECTS {lastupdated: 1}]->(snapshot)
        MERGE (finding)-[:AFFECTS {lastupdated: 1}]->(image)
        MERGE (package)-[:DEPLOYED {lastupdated: 1}]->(snapshot)
        MERGE (package)-[:DEPLOYED {lastupdated: 1}]->(image)
        """
    )

    cleanup_filesystem_snapshot_relationships(neo4j_session, update_tag=2)

    assert (
        check_rels(
            neo4j_session,
            "TrivyImageFinding",
            "id",
            "FilesystemSnapshot",
            "id",
            "AFFECTS",
            rel_direction_right=True,
        )
        == set()
    )
    assert check_rels(
        neo4j_session,
        "TrivyImageFinding",
        "id",
        "Image",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {("cleanup-finding", "cleanup-image")}
    assert (
        check_rels(
            neo4j_session,
            "TrivyPackage",
            "id",
            "FilesystemSnapshot",
            "id",
            "DEPLOYED",
            rel_direction_right=True,
        )
        == set()
    )
    assert check_rels(
        neo4j_session,
        "TrivyPackage",
        "id",
        "Image",
        "id",
        "DEPLOYED",
        rel_direction_right=True,
    ) == {("cleanup-package", "cleanup-image")}


def test_image_cleanup_preserves_filesystem_relationships(neo4j_session):
    # Arrange
    neo4j_session.run(
        """
        MERGE (snapshot:FilesystemSnapshot {id: "cleanup-snapshot"})
        MERGE (image:Image {id: "cleanup-image"})
        MERGE (finding:TrivyImageFinding {id: "cleanup-finding"})
        MERGE (package:TrivyPackage {id: "cleanup-package"})
        MERGE (finding)-[:AFFECTS {lastupdated: 1}]->(snapshot)
        MERGE (finding)-[:AFFECTS {lastupdated: 1}]->(image)
        MERGE (package)-[:DEPLOYED {lastupdated: 1}]->(snapshot)
        MERGE (package)-[:DEPLOYED {lastupdated: 1}]->(image)
        """
    )

    # Act
    cleanup_image_relationships(neo4j_session, update_tag=2)

    # Assert
    assert (
        check_rels(
            neo4j_session,
            "TrivyImageFinding",
            "id",
            "Image",
            "id",
            "AFFECTS",
            rel_direction_right=True,
        )
        == set()
    )
    assert check_rels(
        neo4j_session,
        "TrivyImageFinding",
        "id",
        "FilesystemSnapshot",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {("cleanup-finding", "cleanup-snapshot")}
    assert (
        check_rels(
            neo4j_session,
            "TrivyPackage",
            "id",
            "Image",
            "id",
            "DEPLOYED",
            rel_direction_right=True,
        )
        == set()
    )
    assert check_rels(
        neo4j_session,
        "TrivyPackage",
        "id",
        "FilesystemSnapshot",
        "id",
        "DEPLOYED",
        rel_direction_right=True,
    ) == {("cleanup-package", "cleanup-snapshot")}
