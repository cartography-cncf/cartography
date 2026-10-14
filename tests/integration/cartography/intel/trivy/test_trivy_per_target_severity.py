import json

from cartography.intel.common.object_store import LocalReportReader
from cartography.intel.trivy import sync_trivy_from_report_reader
from cartography.intel.trivy.scanner import cleanup_image_relationships
from cartography.intel.trivy.scanner import sync_single_image
from tests.data.trivy.trivy_sample import PER_TARGET_DIGEST_A
from tests.data.trivy.trivy_sample import PER_TARGET_DIGEST_B
from tests.data.trivy.trivy_sample import TRIVY_MULTI_PACKAGE_REPORT
from tests.data.trivy.trivy_sample import TRIVY_PER_TARGET_REPORT_A
from tests.data.trivy.trivy_sample import TRIVY_PER_TARGET_REPORT_A_UNSOURCED
from tests.data.trivy.trivy_sample import TRIVY_PER_TARGET_REPORT_B
from tests.integration.cartography.intel.trivy.test_helpers import (
    assert_trivy_affects_rel_properties,
)
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


def _sync_both_images(neo4j_session, update_tag: int) -> None:
    sync_single_image(
        neo4j_session,
        TRIVY_PER_TARGET_REPORT_A,
        "report-a.json",
        update_tag,
    )
    sync_single_image(
        neo4j_session,
        TRIVY_PER_TARGET_REPORT_B,
        "report-b.json",
        update_tag,
    )


def _affects_property_keys(neo4j_session, digest: str) -> set[str]:
    record = neo4j_session.run(
        """
        MATCH (:TrivyImageFinding {id: $finding_id})-[r:AFFECTS]->(:Image {_ont_digest: $digest})
        RETURN keys(r) AS keys
        """,
        finding_id=FINDING_ID,
        digest=digest,
    ).single()
    return set(record["keys"])


def test_affects_carries_each_image_rating(neo4j_session):
    # Arrange
    _reset_graph_with_images(neo4j_session)

    # Act
    _sync_both_images(neo4j_session, TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "TrivyImageFinding", ["id"]) == {(FINDING_ID,)}
    assert_trivy_affects_rel_properties(
        neo4j_session,
        "Image",
        "_ont_digest",
        {
            (FINDING_ID, PER_TARGET_DIGEST_A, "LOW", "debian", "affected", "debian"),
            (FINDING_ID, PER_TARGET_DIGEST_B, "HIGH", "nvd", "fixed", "alpine"),
        },
    )
    # The shared node still takes the last-ingested package row.
    assert check_nodes(
        neo4j_session,
        "TrivyImageFinding",
        ["severity", "severity_source", "status", "data_source_id"],
    ) == {("HIGH", "nvd", "fixed", "alpine")}


def test_resync_refreshes_the_image_rating_and_drops_a_missing_source(
    neo4j_session,
):
    # Arrange
    _reset_graph_with_images(neo4j_session)
    _sync_both_images(neo4j_session, TEST_UPDATE_TAG)

    # Act
    sync_single_image(
        neo4j_session,
        TRIVY_PER_TARGET_REPORT_A_UNSOURCED,
        "report-a.json",
        NEXT_UPDATE_TAG,
    )

    # Assert
    assert_trivy_affects_rel_properties(
        neo4j_session,
        "Image",
        "_ont_digest",
        {
            (FINDING_ID, PER_TARGET_DIGEST_A, "MEDIUM", None, "affected", "debian"),
            (FINDING_ID, PER_TARGET_DIGEST_B, "HIGH", "nvd", "fixed", "alpine"),
        },
    )
    assert "severity_source" not in _affects_property_keys(
        neo4j_session,
        PER_TARGET_DIGEST_A,
    )


def test_cleanup_removes_the_rating_of_an_image_missing_from_the_scan(
    neo4j_session,
):
    # Arrange
    _reset_graph_with_images(neo4j_session)
    _sync_both_images(neo4j_session, TEST_UPDATE_TAG)
    sync_single_image(
        neo4j_session,
        TRIVY_PER_TARGET_REPORT_A,
        "report-a.json",
        NEXT_UPDATE_TAG,
    )

    # Act
    cleanup_image_relationships(neo4j_session, NEXT_UPDATE_TAG)

    # Assert
    assert_trivy_affects_rel_properties(
        neo4j_session,
        "Image",
        "_ont_digest",
        {
            (FINDING_ID, PER_TARGET_DIGEST_A, "LOW", "debian", "affected", "debian"),
        },
    )


def test_multi_package_image_takes_its_worst_package_rating(neo4j_session):
    # Arrange
    _reset_graph_with_images(neo4j_session)
    # The worse package comes first, so the edge would keep the LOW rating if the
    # last package row still decided it.
    worst_package_first = {
        **TRIVY_MULTI_PACKAGE_REPORT,
        "Results": TRIVY_MULTI_PACKAGE_REPORT["Results"][::-1],
    }

    # Act
    sync_single_image(
        neo4j_session,
        worst_package_first,
        "multi-package.json",
        TEST_UPDATE_TAG,
    )

    # Assert
    assert_trivy_affects_rel_properties(
        neo4j_session,
        "Image",
        "_ont_digest",
        {(FINDING_ID, PER_TARGET_DIGEST_A, "HIGH", "ghsa", "fixed", "ghsa")},
    )


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
    assert_trivy_affects_rel_properties(
        neo4j_session,
        "FilesystemSnapshot",
        "id",
        {
            (FINDING_ID, SNAPSHOT_IDS[0], "HIGH", "ghsa", "fixed", "ghsa"),
            (FINDING_ID, SNAPSHOT_IDS[1], "HIGH", "ghsa", "fixed", "ghsa"),
        },
    )
