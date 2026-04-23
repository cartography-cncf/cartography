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
from tests.data.gcp.cloudrun import MOCK_SERVICES
from tests.data.gcp.cloudrun import TEST_JOB_PRIMARY_DIGEST
from tests.data.gcp.cloudrun import TEST_REVISION_PRIMARY_DIGEST
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"
TEST_SERVICE_ID = "projects/test-project/locations/us-central1/services/test-service"
TEST_REVISION_ID = "projects/test-project/locations/us-central1/services/test-service/revisions/test-service-00001-abc"
TEST_JOB_ID = "projects/test-project/locations/us-west1/jobs/test-job"


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
    then verify RESOLVED_IMAGE is created on the :Function side (Service via
    HAS_REVISION traversal; Job directly).

    Revision has no ontology label of its own and must not carry RESOLVED_IMAGE.
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
    mock_get_services.return_value = MOCK_SERVICES["services"]
    mock_get_revisions.return_value = MOCK_REVISION_WITH_DIGEST
    mock_get_jobs.return_value = MOCK_JOB_WITH_DIGEST
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    mock_client = MagicMock()

    cloudrun_service.sync_services(
        neo4j_session,
        mock_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cloudrun_revision.sync_revisions(
        neo4j_session,
        mock_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cloudrun_job.sync_jobs(
        neo4j_session,
        mock_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act: run the RESOLVED_IMAGE analysis job
    run_analysis_job(
        "resolved_image_analysis.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert: RESOLVED_IMAGE edges exist on :Function for both Service (via HAS_REVISION) and Job (directly).
    assert check_rels(
        neo4j_session,
        "Function",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {
        (TEST_SERVICE_ID, TEST_REVISION_PRIMARY_DIGEST),
        (TEST_JOB_ID, TEST_JOB_PRIMARY_DIGEST),
    }

    # Assert: Revision itself has no RESOLVED_IMAGE (it is not an ontology node).
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
