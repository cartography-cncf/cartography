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
from tests.data.gcp.cloudrun import MOCK_SERVICE_WITH_DIGEST
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
TEST_CLOUD_RUN_LOCATIONS = [
    "projects/test-project/locations/us-central1",
    "projects/test-project/locations/us-west1",
]
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
    mock_credentials = MagicMock()

    # Act: Sync all Cloud Run resources
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

    cloudrun_execution.sync_executions(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
        TEST_CLOUD_RUN_LOCATIONS,
        mock_credentials,
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
@patch("cartography.intel.gcp.cloudrun.service.get_services")
def test_cloud_run_image_prerequisites(
    mock_get_services,
    mock_get_revisions,
    mock_get_jobs,
    neo4j_session,
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    mock_get_services.return_value = MOCK_SERVICE_WITH_DIGEST
    mock_get_revisions.return_value = MOCK_REVISION_WITH_DIGEST
    mock_get_jobs.return_value = MOCK_JOB_WITH_DIGEST

    _create_prerequisite_nodes(neo4j_session)
    _create_image_registry_nodes(neo4j_session)

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

    # Container nodes from Service (latestReadyRevision spec) and Job (task template).
    service_primary_container_id = f"{TEST_SERVICE_ID}/containers/0"
    service_sidecar_container_id = f"{TEST_SERVICE_ID}/containers/1"
    job_primary_container_id = f"{TEST_JOB_ID}/containers/0"
    job_sidecar_container_id = f"{TEST_JOB_ID}/containers/1"

    # Service-side and Job-side use distinct schemas; both carry :Container.
    assert check_nodes(
        neo4j_session,
        "GCPCloudRunServiceContainer",
        ["id", "image", "image_digest"],
    ) == {
        (
            service_primary_container_id,
            TEST_REVISION_PRIMARY_IMAGE,
            TEST_REVISION_PRIMARY_DIGEST,
        ),
        (
            service_sidecar_container_id,
            TEST_REVISION_SIDECAR_IMAGE,
            TEST_REVISION_SIDECAR_DIGEST,
        ),
    }
    assert check_nodes(
        neo4j_session,
        "GCPCloudRunJobContainer",
        ["id", "image", "image_digest"],
    ) == {
        (job_primary_container_id, TEST_JOB_PRIMARY_IMAGE, TEST_JOB_PRIMARY_DIGEST),
        (job_sidecar_container_id, TEST_JOB_SIDECAR_IMAGE, TEST_JOB_SIDECAR_DIGEST),
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunService",
        "id",
        "GCPCloudRunServiceContainer",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {
        (TEST_SERVICE_ID, service_primary_container_id),
        (TEST_SERVICE_ID, service_sidecar_container_id),
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunJob",
        "id",
        "GCPCloudRunJobContainer",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {
        (TEST_JOB_ID, job_primary_container_id),
        (TEST_JOB_ID, job_sidecar_container_id),
    }

    # Revision is now a pure versioning marker; no HAS_IMAGE on it.
    assert (
        check_rels(
            neo4j_session,
            "GCPCloudRunRevision",
            "id",
            "ECRImage",
            "digest",
            "HAS_IMAGE",
        )
        == set()
    )

    # HAS_IMAGE rels are split per-schema; using :Container collapses both back.
    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "ECRImage",
        "digest",
        "HAS_IMAGE",
    ) == {
        (service_primary_container_id, TEST_REVISION_PRIMARY_DIGEST),
        (service_sidecar_container_id, TEST_REVISION_SIDECAR_DIGEST),
        (job_primary_container_id, TEST_JOB_PRIMARY_DIGEST),
        (job_sidecar_container_id, TEST_JOB_SIDECAR_DIGEST),
    }

    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "GitLabContainerImage",
        "digest",
        "HAS_IMAGE",
    ) == {
        (service_primary_container_id, TEST_REVISION_PRIMARY_DIGEST),
        (service_sidecar_container_id, TEST_REVISION_SIDECAR_DIGEST),
        (job_primary_container_id, TEST_JOB_PRIMARY_DIGEST),
        (job_sidecar_container_id, TEST_JOB_SIDECAR_DIGEST),
    }

    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "GCPArtifactRegistryContainerImage",
        "digest",
        "HAS_IMAGE",
    ) == {
        (service_primary_container_id, TEST_REVISION_PRIMARY_DIGEST),
        (service_sidecar_container_id, TEST_REVISION_SIDECAR_DIGEST),
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

    # Cloud Run Service/Job container specs are declarative; the ontology mapping encodes
    # _ont_state="running" statically so :Container consumers can uniformly query containers
    # that are running or can be launched.
    service_container_states = neo4j_session.run(
        """
        MATCH (c:GCPCloudRunServiceContainer)
        RETURN c.id AS id, c._ont_state AS state
        """,
    )
    assert {(r["id"], r["state"]) for r in service_container_states} == {
        (service_primary_container_id, "running"),
        (service_sidecar_container_id, "running"),
    }
    job_container_states = neo4j_session.run(
        """
        MATCH (c:GCPCloudRunJobContainer)
        RETURN c.id AS id, c._ont_state AS state
        """,
    )
    assert {(r["id"], r["state"]) for r in job_container_states} == {
        (job_primary_container_id, "running"),
        (job_sidecar_container_id, "running"),
    }
