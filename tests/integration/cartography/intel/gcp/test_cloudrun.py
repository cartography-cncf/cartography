from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.cloudrun.execution as cloudrun_execution
import cartography.intel.gcp.cloudrun.job as cloudrun_job
import cartography.intel.gcp.cloudrun.revision as cloudrun_revision
import cartography.intel.gcp.cloudrun.service as cloudrun_service
from tests.data.gcp.cloudrun import MOCK_EXECUTIONS
from tests.data.gcp.cloudrun import MOCK_JOB_WITH_DIGEST
from tests.data.gcp.cloudrun import MOCK_JOBS
from tests.data.gcp.cloudrun import MOCK_REVISION_WITH_DIGEST
from tests.data.gcp.cloudrun import MOCK_REVISIONS
from tests.data.gcp.cloudrun import MOCK_SERVICES
from tests.data.gcp.cloudrun import TEST_JOB_PRIMARY_DIGEST
from tests.data.gcp.cloudrun import TEST_JOB_SIDECAR_DIGEST
from tests.data.gcp.cloudrun import TEST_REVISION_PRIMARY_DIGEST
from tests.data.gcp.cloudrun import TEST_REVISION_SIDECAR_DIGEST
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"
TEST_SERVICE_ID = "projects/test-project/locations/us-central1/services/test-service"
TEST_REVISION_ID = "projects/test-project/locations/us-central1/services/test-service/revisions/test-service-00001-abc"
TEST_JOB_ID = "projects/test-project/locations/us-west1/jobs/test-job"
TEST_EXECUTION_ID_1 = "projects/test-project/locations/us-west1/jobs/test-job/executions/test-job-exec-001"
TEST_EXECUTION_ID_2 = "projects/test-project/locations/us-west1/jobs/test-job/executions/test-job-exec-002"
TEST_SA_EMAIL_1 = "test-sa@test-project.iam.gserviceaccount.com"
TEST_SA_EMAIL_2 = "batch-sa@test-project.iam.gserviceaccount.com"
TEST_REVISION_PRIMARY_IMAGE = (
    "us-central1-docker.pkg.dev/test-project/runtime-repo/test-image"
    f"@{TEST_REVISION_PRIMARY_DIGEST}"
)
TEST_REVISION_SIDECAR_IMAGE = (
    "us-central1-docker.pkg.dev/test-project/runtime-repo/log-sidecar"
    f"@{TEST_REVISION_SIDECAR_DIGEST}"
)
TEST_JOB_PRIMARY_IMAGE = (
    "us-west1-docker.pkg.dev/test-project/runtime-repo/batch-processor"
    f"@{TEST_JOB_PRIMARY_DIGEST}"
)
TEST_JOB_SIDECAR_IMAGE = (
    "us-west1-docker.pkg.dev/test-project/runtime-repo/otel-sidecar"
    f"@{TEST_JOB_SIDECAR_DIGEST}"
)
TEST_REVISION_PRIMARY_ARTIFACT_IMAGE_ID = (
    "projects/test-project/locations/us-central1/repositories/runtime-repo/"
    f"dockerImages/test-image@{TEST_REVISION_PRIMARY_DIGEST}"
)
TEST_REVISION_SIDECAR_ARTIFACT_IMAGE_ID = (
    "projects/test-project/locations/us-central1/repositories/runtime-repo/"
    f"dockerImages/log-sidecar@{TEST_REVISION_SIDECAR_DIGEST}"
)
TEST_REVISION_PRIMARY_PLATFORM_DIGEST = (
    "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
)
TEST_REVISION_SIDECAR_PLATFORM_DIGEST = (
    "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
)
TEST_REVISION_PRIMARY_PLATFORM_IMAGE_ID = (
    f"{TEST_REVISION_PRIMARY_ARTIFACT_IMAGE_ID}@{TEST_REVISION_PRIMARY_PLATFORM_DIGEST}"
)
TEST_REVISION_SIDECAR_PLATFORM_IMAGE_ID = (
    f"{TEST_REVISION_SIDECAR_ARTIFACT_IMAGE_ID}@{TEST_REVISION_SIDECAR_PLATFORM_DIGEST}"
)
TEST_JOB_PRIMARY_ARTIFACT_IMAGE_ID = (
    "projects/test-project/locations/us-west1/repositories/runtime-repo/"
    f"dockerImages/batch-processor@{TEST_JOB_PRIMARY_DIGEST}"
)
TEST_JOB_SIDECAR_ARTIFACT_IMAGE_ID = (
    "projects/test-project/locations/us-west1/repositories/runtime-repo/"
    f"dockerImages/otel-sidecar@{TEST_JOB_SIDECAR_DIGEST}"
)


def _create_prerequisite_nodes(neo4j_session):
    """
    Create nodes that the Cloud Run sync expects to already exist.
    """
    neo4j_session.run(
        "MERGE (p:GCPProject {id: $project_id}) SET p.lastupdated = $tag",
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (sa:GCPServiceAccount {email: $sa_email}) SET sa.lastupdated = $tag",
        sa_email=TEST_SA_EMAIL_1,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (sa:GCPServiceAccount {email: $sa_email}) SET sa.lastupdated = $tag",
        sa_email=TEST_SA_EMAIL_2,
        tag=TEST_UPDATE_TAG,
    )


def _create_image_registry_nodes(neo4j_session):
    for digest in (
        TEST_REVISION_PRIMARY_DIGEST,
        TEST_REVISION_SIDECAR_DIGEST,
        TEST_JOB_PRIMARY_DIGEST,
        TEST_JOB_SIDECAR_DIGEST,
    ):
        neo4j_session.run(
            """
            MERGE (img:ECRImage {id: $digest, digest: $digest})
            SET img.lastupdated = $tag
            """,
            digest=digest,
            tag=TEST_UPDATE_TAG,
        )
        neo4j_session.run(
            """
            MERGE (img:GitLabContainerImage {id: $digest, digest: $digest})
            SET img.lastupdated = $tag
            """,
            digest=digest,
            tag=TEST_UPDATE_TAG,
        )

    neo4j_session.run(
        """
        MERGE (img:GCPArtifactRegistryContainerImage {id: $id})
        SET img.digest = $digest,
            img.name = $name,
            img.uri = $uri,
            img.repository_id = 'projects/test-project/locations/us-central1/repositories/runtime-repo',
            img.project_id = $project_id,
            img.media_type = 'application/vnd.oci.image.index.v1+json',
            img.lastupdated = $tag
        """,
        id=TEST_REVISION_PRIMARY_ARTIFACT_IMAGE_ID,
        digest=TEST_REVISION_PRIMARY_DIGEST,
        name="test-image",
        uri=TEST_REVISION_PRIMARY_IMAGE,
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (img:GCPArtifactRegistryPlatformImage {id: $id})
        SET img.digest = $digest,
            img.parent_artifact_id = $parent_artifact_id,
            img.architecture = 'amd64',
            img.os = 'linux',
            img.project_id = $project_id,
            img.lastupdated = $tag
        """,
        id=TEST_REVISION_PRIMARY_PLATFORM_IMAGE_ID,
        digest=TEST_REVISION_PRIMARY_PLATFORM_DIGEST,
        parent_artifact_id=TEST_REVISION_PRIMARY_ARTIFACT_IMAGE_ID,
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (img:GCPArtifactRegistryPlatformImage {id: $id})
        SET img.digest = $digest,
            img.parent_artifact_id = $parent_artifact_id,
            img.architecture = 'amd64',
            img.os = 'linux',
            img.project_id = $project_id,
            img.lastupdated = $tag
        """,
        id=TEST_REVISION_SIDECAR_PLATFORM_IMAGE_ID,
        digest=TEST_REVISION_SIDECAR_PLATFORM_DIGEST,
        parent_artifact_id=TEST_REVISION_SIDECAR_ARTIFACT_IMAGE_ID,
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (img:GCPArtifactRegistryContainerImage {id: $id})
        SET img.digest = $digest,
            img.name = $name,
            img.uri = $uri,
            img.repository_id = 'projects/test-project/locations/us-central1/repositories/runtime-repo',
            img.project_id = $project_id,
            img.media_type = 'application/vnd.oci.image.index.v1+json',
            img.lastupdated = $tag
        """,
        id=TEST_REVISION_SIDECAR_ARTIFACT_IMAGE_ID,
        digest=TEST_REVISION_SIDECAR_DIGEST,
        name="log-sidecar",
        uri=TEST_REVISION_SIDECAR_IMAGE,
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (img:GCPArtifactRegistryContainerImage {id: $id})
        SET img.digest = $digest,
            img.name = $name,
            img.uri = $uri,
            img.repository_id = 'projects/test-project/locations/us-west1/repositories/runtime-repo',
            img.project_id = $project_id,
            img.media_type = 'application/vnd.oci.image.manifest.v1+json',
            img.lastupdated = $tag
        """,
        id=TEST_JOB_PRIMARY_ARTIFACT_IMAGE_ID,
        digest=TEST_JOB_PRIMARY_DIGEST,
        name="batch-processor",
        uri=TEST_JOB_PRIMARY_IMAGE,
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (img:GCPArtifactRegistryContainerImage {id: $id})
        SET img.digest = $digest,
            img.name = $name,
            img.uri = $uri,
            img.repository_id = 'projects/test-project/locations/us-west1/repositories/runtime-repo',
            img.project_id = $project_id,
            img.media_type = 'application/vnd.oci.image.manifest.v1+json',
            img.lastupdated = $tag
        """,
        id=TEST_JOB_SIDECAR_ARTIFACT_IMAGE_ID,
        digest=TEST_JOB_SIDECAR_DIGEST,
        name="otel-sidecar",
        uri=TEST_JOB_SIDECAR_IMAGE,
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )


def _get_cloud_run_node_image_metadata(
    neo4j_session,
    node_label: str,
    node_id: str,
):
    result = neo4j_session.run(
        f"""
        MATCH (n:{node_label} {{id: $node_id}})
        RETURN
            n.container_image AS container_image,
            n.container_images AS container_images,
            n.image_digest AS image_digest,
            n.image_digests AS image_digests,
            n.architecture AS architecture,
            n.architecture_normalized AS architecture_normalized,
            n.architecture_source AS architecture_source
        """,
        node_id=node_id,
    ).single()
    assert result is not None
    return {
        "container_image": result["container_image"],
        "container_images": result["container_images"],
        "image_digest": result["image_digest"],
        "image_digests": result["image_digests"],
        "architecture": result["architecture"],
        "architecture_normalized": result["architecture_normalized"],
        "architecture_source": result["architecture_source"],
    }


@patch("cartography.intel.gcp.cloudrun.execution.get_executions")
@patch("cartography.intel.gcp.cloudrun.job.get_jobs")
@patch("cartography.intel.gcp.cloudrun.revision.get_revisions")
@patch("cartography.intel.gcp.cloudrun.service.get_services")
def test_sync_cloudrun(
    mock_get_services,
    mock_get_revisions,
    mock_get_jobs,
    mock_get_executions,
    neo4j_session,
):
    """
    Test the full sync() functions for the GCP Cloud Run modules.
    This test simulates the behavior of the main gcp/__init__.py file.
    """
    # Clear the entire database to start fresh
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Arrange: Mock all 4 API calls
    mock_get_services.return_value = MOCK_SERVICES["services"]
    mock_get_revisions.return_value = MOCK_REVISIONS["revisions"]
    mock_get_jobs.return_value = MOCK_JOBS["jobs"]
    mock_get_executions.return_value = MOCK_EXECUTIONS["executions"]

    # Arrange: Create prerequisite nodes
    _create_prerequisite_nodes(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    mock_client = MagicMock()

    # Act: Sync all Cloud Run resources
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

    cloudrun_execution.sync_executions(
        neo4j_session,
        mock_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: Check all 4 node types
    assert check_nodes(neo4j_session, "GCPCloudRunService", ["id"]) == {
        (TEST_SERVICE_ID,),
    }
    assert check_nodes(neo4j_session, "GCPCloudRunService", ["id", "ingress"]) == {
        (TEST_SERVICE_ID, "INGRESS_TRAFFIC_ALL"),
    }
    assert check_nodes(neo4j_session, "GCPCloudRunRevision", ["id"]) == {
        (TEST_REVISION_ID,),
    }
    assert check_nodes(neo4j_session, "GCPCloudRunJob", ["id"]) == {
        (TEST_JOB_ID,),
    }
    assert check_nodes(neo4j_session, "GCPCloudRunExecution", ["id"]) == {
        (TEST_EXECUTION_ID_1,),
        (TEST_EXECUTION_ID_2,),
    }

    # Assert: Check Cloud Run specific relationships
    assert check_rels(
        neo4j_session,
        "GCPCloudRunService",
        "id",
        "GCPCloudRunRevision",
        "id",
        "HAS_REVISION",
    ) == {(TEST_SERVICE_ID, TEST_REVISION_ID)}

    assert check_rels(
        neo4j_session,
        "GCPCloudRunJob",
        "id",
        "GCPCloudRunExecution",
        "id",
        "HAS_EXECUTION",
    ) == {
        (TEST_JOB_ID, TEST_EXECUTION_ID_1),
        (TEST_JOB_ID, TEST_EXECUTION_ID_2),
    }

    # Assert: Check service account relationships
    assert check_rels(
        neo4j_session,
        "GCPCloudRunService",
        "id",
        "GCPServiceAccount",
        "email",
        "USES_SERVICE_ACCOUNT",
    ) == {(TEST_SERVICE_ID, TEST_SA_EMAIL_1)}

    assert check_rels(
        neo4j_session,
        "GCPCloudRunRevision",
        "id",
        "GCPServiceAccount",
        "email",
        "USES_SERVICE_ACCOUNT",
    ) == {(TEST_REVISION_ID, TEST_SA_EMAIL_1)}

    assert check_rels(
        neo4j_session,
        "GCPCloudRunJob",
        "id",
        "GCPServiceAccount",
        "email",
        "USES_SERVICE_ACCOUNT",
    ) == {(TEST_JOB_ID, TEST_SA_EMAIL_2)}

    # Assert: Check GCPLabel nodes from Cloud Run service labels
    assert check_nodes(neo4j_session, "GCPLabel", ["key", "value"]) >= {
        ("env", "prod"),
        ("team", "api"),
    }

    # Assert: Check LABELED relationships
    assert check_rels(
        neo4j_session,
        "GCPCloudRunService",
        "id",
        "GCPLabel",
        "id",
        "LABELED",
        rel_direction_right=True,
    ) == {
        (TEST_SERVICE_ID, f"{TEST_SERVICE_ID}:env:prod"),
        (TEST_SERVICE_ID, f"{TEST_SERVICE_ID}:team:api"),
    }

    # Assert: Check GCPLabel nodes from Cloud Run job labels
    assert check_nodes(neo4j_session, "GCPLabel", ["key", "value"]) >= {
        ("env", "staging"),
        ("team", "batch"),
    }

    # Assert: Check LABELED relationships for jobs
    assert check_rels(
        neo4j_session,
        "GCPCloudRunJob",
        "id",
        "GCPLabel",
        "id",
        "LABELED",
        rel_direction_right=True,
    ) == {
        (TEST_JOB_ID, f"{TEST_JOB_ID}:env:staging"),
        (TEST_JOB_ID, f"{TEST_JOB_ID}:team:batch"),
    }


@patch("cartography.intel.gcp.cloudrun.job.get_jobs")
@patch("cartography.intel.gcp.cloudrun.revision.get_revisions")
def test_cloud_run_image_prerequisites(
    mock_get_revisions,
    mock_get_jobs,
    neo4j_session,
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    mock_get_revisions.return_value = MOCK_REVISION_WITH_DIGEST
    mock_get_jobs.return_value = MOCK_JOB_WITH_DIGEST

    _create_prerequisite_nodes(neo4j_session)
    _create_image_registry_nodes(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    mock_client = MagicMock()

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

    assert _get_cloud_run_node_image_metadata(
        neo4j_session,
        "GCPCloudRunRevision",
        TEST_REVISION_ID,
    ) == {
        "container_image": TEST_REVISION_PRIMARY_IMAGE,
        "container_images": [TEST_REVISION_PRIMARY_IMAGE, TEST_REVISION_SIDECAR_IMAGE],
        "image_digest": TEST_REVISION_PRIMARY_DIGEST,
        "image_digests": [TEST_REVISION_PRIMARY_DIGEST, TEST_REVISION_SIDECAR_DIGEST],
        "architecture": "amd64",
        "architecture_normalized": "amd64",
        "architecture_source": "platform_requirement",
    }

    # Job is now a pure grouping node: image/architecture live on the child GCPCloudRunContainer.
    job_primary_container_id = f"{TEST_JOB_ID}/containers/0"
    job_sidecar_container_id = f"{TEST_JOB_ID}/containers/1"
    assert check_nodes(
        neo4j_session,
        "GCPCloudRunContainer",
        ["id", "image", "image_digest"],
    ) == {
        (job_primary_container_id, TEST_JOB_PRIMARY_IMAGE, TEST_JOB_PRIMARY_DIGEST),
        (job_sidecar_container_id, TEST_JOB_SIDECAR_IMAGE, TEST_JOB_SIDECAR_DIGEST),
    }
    assert check_rels(
        neo4j_session,
        "GCPCloudRunJob",
        "id",
        "GCPCloudRunContainer",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {
        (TEST_JOB_ID, job_primary_container_id),
        (TEST_JOB_ID, job_sidecar_container_id),
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunRevision",
        "id",
        "ECRImage",
        "digest",
        "HAS_IMAGE",
    ) == {
        (TEST_REVISION_ID, TEST_REVISION_PRIMARY_DIGEST),
        (TEST_REVISION_ID, TEST_REVISION_SIDECAR_DIGEST),
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunContainer",
        "id",
        "ECRImage",
        "digest",
        "HAS_IMAGE",
    ) == {
        (job_primary_container_id, TEST_JOB_PRIMARY_DIGEST),
        (job_sidecar_container_id, TEST_JOB_SIDECAR_DIGEST),
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunRevision",
        "id",
        "GitLabContainerImage",
        "digest",
        "HAS_IMAGE",
    ) == {
        (TEST_REVISION_ID, TEST_REVISION_PRIMARY_DIGEST),
        (TEST_REVISION_ID, TEST_REVISION_SIDECAR_DIGEST),
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunContainer",
        "id",
        "GitLabContainerImage",
        "digest",
        "HAS_IMAGE",
    ) == {
        (job_primary_container_id, TEST_JOB_PRIMARY_DIGEST),
        (job_sidecar_container_id, TEST_JOB_SIDECAR_DIGEST),
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunRevision",
        "id",
        "GCPArtifactRegistryContainerImage",
        "digest",
        "HAS_IMAGE",
    ) == {
        (TEST_REVISION_ID, TEST_REVISION_PRIMARY_DIGEST),
        (TEST_REVISION_ID, TEST_REVISION_SIDECAR_DIGEST),
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunContainer",
        "id",
        "GCPArtifactRegistryContainerImage",
        "digest",
        "HAS_IMAGE",
    ) == {
        (job_primary_container_id, TEST_JOB_PRIMARY_DIGEST),
        (job_sidecar_container_id, TEST_JOB_SIDECAR_DIGEST),
    }

    assert check_nodes(
        neo4j_session,
        "GCPArtifactRegistryPlatformImage",
        ["id", "parent_artifact_id"],
    ) >= {
        (
            TEST_REVISION_PRIMARY_PLATFORM_IMAGE_ID,
            TEST_REVISION_PRIMARY_ARTIFACT_IMAGE_ID,
        ),
        (
            TEST_REVISION_SIDECAR_PLATFORM_IMAGE_ID,
            TEST_REVISION_SIDECAR_ARTIFACT_IMAGE_ID,
        ),
    }

    assert (
        check_rels(
            neo4j_session,
            "GCPCloudRunRevision",
            "id",
            "GCPArtifactRegistryPlatformImage",
            "digest",
            "HAS_IMAGE",
        )
        == set()
    )
