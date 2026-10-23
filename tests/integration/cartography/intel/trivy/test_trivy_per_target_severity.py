import json

from cartography.intel.common.object_store import LocalReportReader
from cartography.intel.trivy import sync_trivy_from_report_reader
from cartography.intel.trivy.scanner import sync_single_filesystem_snapshot
from cartography.intel.trivy.scanner import sync_single_image
from tests.data.trivy.trivy_sample import PER_TARGET_DIGEST_A
from tests.data.trivy.trivy_sample import PER_TARGET_DIGEST_B
from tests.data.trivy.trivy_sample import TRIVY_MULTI_PACKAGE_REPORT
from tests.data.trivy.trivy_sample import TRIVY_PER_TARGET_OS_REPORT_DEBIAN
from tests.data.trivy.trivy_sample import TRIVY_PER_TARGET_OS_REPORT_FILESYSTEM
from tests.data.trivy.trivy_sample import TRIVY_PER_TARGET_OS_REPORT_UBUNTU
from tests.data.trivy.trivy_sample import TRIVY_PER_TARGET_REPORT_A
from tests.data.trivy.trivy_sample import TRIVY_PER_TARGET_REPORT_A_UNSOURCED
from tests.data.trivy.trivy_sample import TRIVY_PER_TARGET_REPORT_B
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
NEXT_UPDATE_TAG = TEST_UPDATE_TAG + 1
FINDING_ID = "TIF|CVE-2023-4039"
SNAPSHOT_IDS = ["snapshot-1", "snapshot-2"]
SOURCE_REVISION = "0123456789abcdef0123456789abcdef01234567"


def _reset_graph_with_images(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        UNWIND $digests AS digest
        MERGE (image:Image {id: digest})
        SET image._ont_digest = digest
        """,
        digests=[PER_TARGET_DIGEST_A, PER_TARGET_DIGEST_B],
    )


def _affects_ratings(neo4j_session, target_label: str) -> set[tuple]:
    result = neo4j_session.run(
        f"""
        MATCH (f:TrivyImageFinding)-[r:AFFECTS]->(t:{target_label})
        RETURN f.id, t.id, r.severity, r.severity_source, r.status, r.data_source_id
        """,
    )
    return {tuple(record.values()) for record in result}


def _deployed_os(neo4j_session) -> set[tuple]:
    result = neo4j_session.run(
        """
        MATCH (p:TrivyPackage)-[r:DEPLOYED]->(t)
        RETURN p.id, t.id, r.os_family, r.os_name, r.os_release
        """,
    )
    return {tuple(record.values()) for record in result}


def test_affects_carries_each_image_rating(neo4j_session):
    # Arrange
    _reset_graph_with_images(neo4j_session)

    # Act
    sync_single_image(
        neo4j_session,
        TRIVY_PER_TARGET_REPORT_A,
        "report-a.json",
        TEST_UPDATE_TAG,
    )
    sync_single_image(
        neo4j_session,
        TRIVY_PER_TARGET_REPORT_B,
        "report-b.json",
        TEST_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(neo4j_session, "TrivyImageFinding", ["id"]) == {(FINDING_ID,)}
    assert _affects_ratings(neo4j_session, "Image") == {
        (FINDING_ID, PER_TARGET_DIGEST_A, "LOW", "debian", "affected", "debian"),
        (FINDING_ID, PER_TARGET_DIGEST_B, "HIGH", "nvd", "fixed", "alpine"),
    }
    # The shared node still takes the last-ingested package row.
    assert check_nodes(
        neo4j_session,
        "TrivyImageFinding",
        ["severity", "severity_source", "status", "data_source_id"],
    ) == {("HIGH", "nvd", "fixed", "alpine")}


def test_rescan_replaces_the_image_rating(neo4j_session):
    # Arrange
    _reset_graph_with_images(neo4j_session)
    sync_single_image(
        neo4j_session,
        TRIVY_PER_TARGET_REPORT_A,
        "report-a.json",
        TEST_UPDATE_TAG,
    )
    sync_single_image(
        neo4j_session,
        TRIVY_PER_TARGET_REPORT_B,
        "report-b.json",
        TEST_UPDATE_TAG,
    )

    # Act
    sync_single_image(
        neo4j_session,
        TRIVY_PER_TARGET_REPORT_A_UNSOURCED,
        "report-a.json",
        NEXT_UPDATE_TAG,
    )

    # Assert
    assert _affects_ratings(neo4j_session, "Image") == {
        (FINDING_ID, PER_TARGET_DIGEST_A, "MEDIUM", None, "affected", "debian"),
        (FINDING_ID, PER_TARGET_DIGEST_B, "HIGH", "nvd", "fixed", "alpine"),
    }


def test_multi_package_image_takes_its_worst_package_rating(neo4j_session):
    # Arrange
    _reset_graph_with_images(neo4j_session)

    # Act
    sync_single_image(
        neo4j_session,
        TRIVY_MULTI_PACKAGE_REPORT,
        "multi-package.json",
        TEST_UPDATE_TAG,
    )

    # Assert
    assert _affects_ratings(neo4j_session, "Image") == {
        (FINDING_ID, PER_TARGET_DIGEST_A, "HIGH", "ghsa", "fixed", "ghsa"),
    }


def test_filesystem_snapshot_affects_carries_the_target_rating(
    neo4j_session,
    tmp_path,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        UNWIND $ids AS id
        MERGE (snapshot:FilesystemSnapshot {id: id})
        SET snapshot.source_repo = "example/api",
            snapshot.source_revision = $revision,
            snapshot.lastupdated = $update_tag
        """,
        ids=SNAPSHOT_IDS,
        revision=SOURCE_REVISION,
        update_tag=TEST_UPDATE_TAG,
    )
    report = {
        "SchemaVersion": 2,
        "ArtifactName": "/src/api",
        "ArtifactType": "repository",
        "Metadata": {
            "RepoURL": "https://github.com/example/api",
            "Commit": SOURCE_REVISION,
        },
        "Results": TRIVY_MULTI_PACKAGE_REPORT["Results"],
    }
    (tmp_path / "repository.json").write_text(json.dumps(report))

    # Act
    sync_trivy_from_report_reader(
        neo4j_session,
        LocalReportReader(str(tmp_path)),
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert _affects_ratings(neo4j_session, "FilesystemSnapshot") == {
        (FINDING_ID, SNAPSHOT_IDS[0], "HIGH", "ghsa", "fixed", "ghsa"),
        (FINDING_ID, SNAPSHOT_IDS[1], "HIGH", "ghsa", "fixed", "ghsa"),
    }


def test_deployed_carries_each_target_os_on_its_os_packages(neo4j_session):
    # Arrange
    _reset_graph_with_images(neo4j_session)
    neo4j_session.run(
        "MERGE (:FilesystemSnapshot {id: $id})",
        id=SNAPSHOT_IDS[0],
    )

    # Act
    sync_single_image(
        neo4j_session,
        TRIVY_PER_TARGET_OS_REPORT_DEBIAN,
        "debian.json",
        TEST_UPDATE_TAG,
    )
    sync_single_image(
        neo4j_session,
        TRIVY_PER_TARGET_OS_REPORT_UBUNTU,
        "ubuntu.json",
        TEST_UPDATE_TAG,
    )
    sync_single_filesystem_snapshot(
        neo4j_session,
        TRIVY_PER_TARGET_OS_REPORT_FILESYSTEM,
        [SNAPSHOT_IDS[0]],
        "rootfs.json",
        TEST_UPDATE_TAG,
    )

    # Assert
    assert _deployed_os(neo4j_session) == {
        ("1.35+dfsg-3|tar", PER_TARGET_DIGEST_A, "debian", "trixie/sid", "13"),
        ("2.31.0|requests", PER_TARGET_DIGEST_A, None, None, None),
        ("1.35+dfsg-3|tar", PER_TARGET_DIGEST_B, "ubuntu", "24.04", None),
        ("1.35+dfsg-3|tar", SNAPSHOT_IDS[0], "debian", "12.13", "12"),
    }
