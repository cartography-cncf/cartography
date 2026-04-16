"""
Integration test for the Container -> Image RESOLVED_IMAGE analysis job.
"""

from cartography.util import run_analysis_job
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def test_resolved_image_analysis_creates_rel_via_has_image(neo4j_session):
    """The analysis job should create RESOLVED_IMAGE from :Container to :Image over an existing HAS_IMAGE edge."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (c:Container:KubernetesContainer {id: 'container-1'})
        SET c._ont_image_digest = 'sha256:deadbeef',
            c.lastupdated = $update_tag

        MERGE (i:Image:ECRImage {id: 'sha256:deadbeef'})
        SET i._ont_digest = 'sha256:deadbeef',
            i.lastupdated = $update_tag

        MERGE (c)-[r:HAS_IMAGE]->(i)
        SET r.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    run_analysis_job(
        "resolved_image_analysis.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {("container-1", "sha256:deadbeef")}


def test_resolved_image_analysis_creates_rel_for_gcp_cloud_run_revision(neo4j_session):
    """GCPCloudRunRevision carries the :Container label and should participate in RESOLVED_IMAGE."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (c:Container:GCPCloudRunRevision {id: 'revision-1'})
        SET c._ont_image_digest = 'sha256:cloudrundigest',
            c.lastupdated = $update_tag

        MERGE (i:Image:GCPArtifactRegistryContainerImage {id: 'sha256:cloudrundigest'})
        SET i._ont_digest = 'sha256:cloudrundigest',
            i.lastupdated = $update_tag

        MERGE (c)-[r:HAS_IMAGE]->(i)
        SET r.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    run_analysis_job(
        "resolved_image_analysis.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {("revision-1", "sha256:cloudrundigest")}


def test_resolved_image_analysis_creates_rel_for_gcp_cloud_run_job(neo4j_session):
    """GCPCloudRunJob carries both :Function and :Container labels and should participate in RESOLVED_IMAGE."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (c:Container:Function:GCPCloudRunJob {id: 'job-1'})
        SET c._ont_image_digest = 'sha256:jobdigest',
            c.lastupdated = $update_tag

        MERGE (i:Image:ECRImage {id: 'sha256:jobdigest'})
        SET i._ont_digest = 'sha256:jobdigest',
            i.lastupdated = $update_tag

        MERGE (c)-[r:HAS_IMAGE]->(i)
        SET r.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    run_analysis_job(
        "resolved_image_analysis.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {("job-1", "sha256:jobdigest")}


def test_resolved_image_analysis_creates_rel_via_manifest_list(neo4j_session):
    """The analysis job should resolve a Container pointed at an ImageManifestList to the architecture-matching child Image."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (c:Container:ECSContainer {id: 'container-ml-1'})
        SET c.architecture_normalized = 'amd64',
            c.lastupdated = $update_tag

        MERGE (ml:ECRImage:ImageManifestList {id: 'sha256:manifestlist'})
        SET ml.lastupdated = $update_tag

        MERGE (child_amd64:Image:ECRImage {id: 'sha256:childamd64'})
        SET child_amd64._ont_architecture = 'amd64',
            child_amd64.lastupdated = $update_tag

        MERGE (child_arm64:Image:ECRImage {id: 'sha256:childarm64'})
        SET child_arm64._ont_architecture = 'arm64',
            child_arm64.lastupdated = $update_tag

        MERGE (c)-[r:HAS_IMAGE]->(ml)
        SET r.lastupdated = $update_tag

        MERGE (ml)-[r1:CONTAINS_IMAGE]->(child_amd64)
        SET r1.lastupdated = $update_tag

        MERGE (ml)-[r2:CONTAINS_IMAGE]->(child_arm64)
        SET r2.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    run_analysis_job(
        "resolved_image_analysis.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {("container-ml-1", "sha256:childamd64")}
