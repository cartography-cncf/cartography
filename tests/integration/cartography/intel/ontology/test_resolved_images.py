"""
Integration test for the Container/Function -> Image RESOLVED_IMAGE analysis job.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.cloudrun.job as cloudrun_job
import cartography.intel.gcp.cloudrun.revision as cloudrun_revision
import cartography.intel.gcp.cloudrun.service as cloudrun_service
from cartography.util import run_analysis_job
from tests.data.gcp.cloudrun import MOCK_JOB_WITH_DIGEST
from tests.data.gcp.cloudrun import MOCK_REVISION_WITH_DIGEST
from tests.data.gcp.cloudrun import MOCK_SERVICE_WITH_DIGEST
from tests.data.gcp.cloudrun import TEST_JOB_PRIMARY_DIGEST
from tests.data.gcp.cloudrun import TEST_REVISION_PRIMARY_DIGEST
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"
TEST_SERVICE_ID = "projects/test-project/locations/us-central1/services/test-service"
TEST_REVISION_ID = "projects/test-project/locations/us-central1/services/test-service/revisions/test-service-00001-abc"
TEST_JOB_ID = "projects/test-project/locations/us-west1/jobs/test-job"
TEST_CLOUD_RUN_LOCATIONS = [
    "projects/test-project/locations/us-central1",
    "projects/test-project/locations/us-west1",
]


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


@patch("cartography.intel.gcp.cloudrun.service.get_services")
@patch("cartography.intel.gcp.cloudrun.revision.get_revisions")
@patch("cartography.intel.gcp.cloudrun.job.get_jobs")
def test_resolved_image_analysis_creates_rel_for_cloud_run(
    mock_get_jobs,
    mock_get_revisions,
    mock_get_services,
    neo4j_session,
):
    """Run Cloud Run service, revision and job through the real load path,
    then verify RESOLVED_IMAGE is created on the per-container :Container nodes
    for both Service and Job. Service and Job carry no ontology label of their
    own, and Revision is a pure versioning marker — none of them get
    RESOLVED_IMAGE.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Arrange: prerequisite nodes
    neo4j_session.run(
        "MERGE (p:GCPProject {id: $pid}) SET p.lastupdated = $tag",
        pid=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (sa:GCPServiceAccount {email: $e}) SET sa.lastupdated = $tag",
        e="test-sa@test-project.iam.gserviceaccount.com",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (sa:GCPServiceAccount {email: $e}) SET sa.lastupdated = $tag",
        e="batch-sa@test-project.iam.gserviceaccount.com",
        tag=TEST_UPDATE_TAG,
    )

    # Arrange: image nodes that HAS_IMAGE will match (need :Image label for the analysis job)
    neo4j_session.run(
        """
        MERGE (i:Image:ECRImage {id: $digest})
        SET i.digest = $digest, i.lastupdated = $tag
        """,
        digest=TEST_REVISION_PRIMARY_DIGEST,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (i:Image:ECRImage {id: $digest})
        SET i.digest = $digest, i.lastupdated = $tag
        """,
        digest=TEST_JOB_PRIMARY_DIGEST,
        tag=TEST_UPDATE_TAG,
    )

    # Act: sync Cloud Run through the real load path
    mock_get_services.return_value = MOCK_SERVICE_WITH_DIGEST
    mock_get_revisions.return_value = MOCK_REVISION_WITH_DIGEST
    mock_get_jobs.return_value = MOCK_JOB_WITH_DIGEST
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    mock_credentials = MagicMock()

    cloudrun_service.sync_services(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
        TEST_CLOUD_RUN_LOCATIONS,
        mock_credentials,
    )
    cloudrun_revision.sync_revisions(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
        TEST_CLOUD_RUN_LOCATIONS,
        mock_credentials,
    )
    cloudrun_job.sync_jobs(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
        TEST_CLOUD_RUN_LOCATIONS,
        mock_credentials,
    )

    # Act: run the RESOLVED_IMAGE analysis job
    run_analysis_job(
        "resolved_image_analysis.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert: no :Function RESOLVED_IMAGE — Service no longer carries :Function.
    assert (
        check_rels(
            neo4j_session,
            "Function",
            "id",
            "Image",
            "id",
            "RESOLVED_IMAGE",
        )
        == set()
    )

    # Assert: RESOLVED_IMAGE on :Container for both the Service-side and Job-side individual containers.
    service_primary_container_id = f"{TEST_SERVICE_ID}/containers/0"
    job_primary_container_id = f"{TEST_JOB_ID}/containers/0"
    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {
        (service_primary_container_id, TEST_REVISION_PRIMARY_DIGEST),
        (job_primary_container_id, TEST_JOB_PRIMARY_DIGEST),
    }

    # Assert: Revision has no RESOLVED_IMAGE (pure versioning marker).
    assert (
        check_rels(
            neo4j_session,
            "GCPCloudRunRevision",
            "id",
            "Image",
            "id",
            "RESOLVED_IMAGE",
        )
        == set()
    )

    # Assert: Service has no RESOLVED_IMAGE (orchestrator, no ontology label).
    assert (
        check_rels(
            neo4j_session,
            "GCPCloudRunService",
            "id",
            "Image",
            "id",
            "RESOLVED_IMAGE",
        )
        == set()
    )

    # Assert: Job has no RESOLVED_IMAGE (orchestrator, no ontology label).
    assert (
        check_rels(
            neo4j_session,
            "GCPCloudRunJob",
            "id",
            "Image",
            "id",
            "RESOLVED_IMAGE",
        )
        == set()
    )


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


def test_resolved_image_analysis_creates_rel_for_gcp_artifact_registry_manifest_list(
    neo4j_session,
):
    """GAR manifest lists should resolve through CONTAINS_IMAGE to the matching platform image."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (c:Container:GCPCloudRunServiceContainer {id: 'cloud-run-container-1'})
        SET c.architecture_normalized = 'amd64',
            c.lastupdated = $update_tag

        MERGE (ml:GCPArtifactRegistryContainerImage:ImageManifestList {id: 'gar-manifest-list'})
        SET ml.digest = 'sha256:manifestlist',
            ml.lastupdated = $update_tag

        MERGE (child_amd64:GCPArtifactRegistryPlatformImage:Image {id: 'gar-child-amd64'})
        SET child_amd64.digest = 'sha256:childamd64',
            child_amd64._ont_architecture = 'amd64',
            child_amd64.lastupdated = $update_tag

        MERGE (child_arm64:GCPArtifactRegistryPlatformImage:Image {id: 'gar-child-arm64'})
        SET child_arm64.digest = 'sha256:childarm64',
            child_arm64._ont_architecture = 'arm64',
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
    ) == {("cloud-run-container-1", "gar-child-amd64")}
