import json
from copy import deepcopy
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.trivy
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from cartography.intel.common.object_store import ListedReportReader
from cartography.intel.common.object_store import ReportRef
from cartography.intel.trivy.scanner import cleanup_filesystem_snapshot_relationships
from cartography.intel.trivy.scanner import cleanup_image_relationships
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.data.trivy.trivy_vm_sample import TRIVY_VM_SAMPLE
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
SNAPSHOT_IDS = ["railway-deployment-1", "railway-deployment-2"]
SOURCE_REVISION = "0123456789abcdef0123456789abcdef01234567"


@pytest.fixture
def ec2_rootfs_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_account(neo4j_session, "000000000000", TEST_UPDATE_TAG)
    with patch(
        "cartography.intel.aws.ec2.instances.get_ec2_instances",
        return_value=deepcopy(DESCRIBE_INSTANCES["Reservations"]),
    ):
        sync_ec2_instances(
            neo4j_session,
            MagicMock(),
            ["us-east-1"],
            "000000000000",
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": "000000000000"},
        )
    return neo4j_session


def _report_reader(payload):
    ref = ReportRef(uri="memory://report.json", name="report.json")
    return ListedReportReader(
        "memory://trivy-reports", [ref], lambda _ref: json.dumps(payload).encode()
    )


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


def test_sync_trivy_vm_report_to_ec2_filesystem_snapshot(ec2_rootfs_graph):
    # Arrange
    neo4j_session = ec2_rootfs_graph
    payload = deepcopy(TRIVY_VM_SAMPLE)

    # Act
    cartography.intel.trivy.sync_trivy_from_report_reader(
        neo4j_session,
        _report_reader(payload),
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert: real EC2 discovery supplied the ontology fields and instance edges.
    assert check_nodes(
        neo4j_session, "FilesystemSnapshot", ["id", "_ont_kind", "_ont_source"]
    ) == {(f"aws:ec2-rootfs:i-0{i}", "rootfs", "aws") for i in range(1, 5)}
    assert check_rels(
        neo4j_session,
        "ComputeInstance",
        "id",
        "FilesystemSnapshot",
        "id",
        "SCANNED_AS",
        rel_direction_right=True,
    ) == {(f"i-0{i}", f"aws:ec2-rootfs:i-0{i}") for i in range(1, 5)}
    assert check_rels(
        neo4j_session,
        "TrivyImageFinding",
        "id",
        "FilesystemSnapshot",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {("TIF|CVE-2026-12345", "aws:ec2-rootfs:i-01")}
    assert check_rels(
        neo4j_session,
        "TrivyPackage",
        "id",
        "FilesystemSnapshot",
        "id",
        "DEPLOYED",
        rel_direction_right=True,
    ) == {
        ("1.0.0|example-package", "aws:ec2-rootfs:i-01"),
        ("2.0.0|clean-package", "aws:ec2-rootfs:i-01"),
    }

    # Arrange: a later scan uses a different temporary EBS snapshot.
    payload["ArtifactName"] = "ebs:snap-next-scan"

    # Act
    cartography.intel.trivy.sync_trivy_from_report_reader(
        neo4j_session,
        _report_reader(payload),
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1},
    )

    # Assert: the same finding edge is refreshed on the stable target.
    rows = neo4j_session.run(
        """
        MATCH (:ComputeInstance {id: 'i-01'})-[:SCANNED_AS]->(s:FilesystemSnapshot)
              <-[r:AFFECTS]-(f:TrivyImageFinding)
        RETURN s.id AS id, f.id AS finding, r.lastupdated AS updated
        """
    ).data()
    assert rows == [
        {
            "id": "aws:ec2-rootfs:i-01",
            "finding": "TIF|CVE-2026-12345",
            "updated": TEST_UPDATE_TAG + 1,
        }
    ]


@pytest.mark.parametrize(
    "results",
    [
        None,
        [],
        [
            {
                "Class": "os-pkgs",
                "Type": "ubuntu",
                "Vulnerabilities": [],
                "Packages": [{"Name": "clean-package", "Version": "2.0.0"}],
            }
        ],
    ],
)
def test_clean_vm_report_preserves_other_targets(ec2_rootfs_graph, results):
    # Arrange
    neo4j_session = ec2_rootfs_graph
    neo4j_session.run(
        """
        CREATE (:FilesystemSnapshot {id: 'repository-snapshot',
                source_repo: 'acme/api', source_revision: $revision})
        CREATE (:Image {id: 'container-image'})
        WITH 1 AS unused
        MATCH (target)
        WHERE target.id IN ['aws:ec2-rootfs:i-01', 'aws:ec2-rootfs:i-02',
                            'repository-snapshot', 'container-image']
        MERGE (f:TrivyImageFinding {id: 'old-finding', lastupdated: 1})
        MERGE (p:TrivyPackage {id: 'old-package', lastupdated: 1})
        MERGE (f)-[:AFFECTS {lastupdated: 1}]->(target)
        MERGE (p)-[:DEPLOYED {lastupdated: 1}]->(target)
        """,
        revision=SOURCE_REVISION,
    )
    payload = deepcopy(TRIVY_VM_SAMPLE)
    payload["Results"] = results

    # Act
    cartography.intel.trivy.sync_trivy_from_report_reader(
        neo4j_session,
        _report_reader(payload),
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert: only this VM's old findings and packages were removed.
    assert check_rels(
        neo4j_session,
        "TrivyImageFinding",
        "id",
        "FilesystemSnapshot",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("old-finding", "aws:ec2-rootfs:i-02"),
        ("old-finding", "repository-snapshot"),
    }
    expected_packages = {
        ("old-package", "aws:ec2-rootfs:i-02"),
        ("old-package", "repository-snapshot"),
    }
    if results:
        expected_packages.add(("2.0.0|clean-package", "aws:ec2-rootfs:i-01"))
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
        == expected_packages
    )
    for label, edge, node_id in (
        ("TrivyImageFinding", "AFFECTS", "old-finding"),
        ("TrivyPackage", "DEPLOYED", "old-package"),
    ):
        assert check_rels(
            neo4j_session,
            label,
            "id",
            "Image",
            "id",
            edge,
            rel_direction_right=True,
        ) == {(node_id, "container-image")}


@pytest.mark.parametrize(
    "snapshot_id",
    [
        "aws:ec2-rootfs:i-unknown",
        "aws:ec2-rootfs:i-02",
        "unattached-rootfs",
    ],
)
def test_vm_reports_require_a_rootfs_target_on_an_instance(
    ec2_rootfs_graph,
    snapshot_id,
    caplog,
):
    # Arrange: reject unknown IDs, other snapshot kinds, and unattached rootfs.
    neo4j_session = ec2_rootfs_graph
    neo4j_session.run(
        """
        MATCH (s:FilesystemSnapshot {id: 'aws:ec2-rootfs:i-02'})
        SET s._ont_kind = 'source'
        CREATE (:FilesystemSnapshot {id: 'unattached-rootfs', _ont_kind: 'rootfs'})
        CREATE (f:TrivyImageFinding {id: 'existing-finding', lastupdated: 1})
        CREATE (f)-[:AFFECTS {lastupdated: 1}]->(s)
        """
    )
    payload = deepcopy(TRIVY_VM_SAMPLE)
    payload["Metadata"]["FilesystemSnapshotId"] = snapshot_id

    # Act
    cartography.intel.trivy.sync_trivy_from_report_reader(
        neo4j_session,
        _report_reader(payload),
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert: rejection neither creates findings nor cleans up existing evidence.
    assert "Skipping Trivy VM report" in caplog.text
    assert check_nodes(neo4j_session, "TrivyImageFinding", ["id"]) == {
        ("existing-finding",),
    }
    assert check_rels(
        neo4j_session,
        "TrivyImageFinding",
        "id",
        "FilesystemSnapshot",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {("existing-finding", "aws:ec2-rootfs:i-02")}
