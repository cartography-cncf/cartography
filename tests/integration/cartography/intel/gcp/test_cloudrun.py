from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.cloudrun.execution as cloudrun_execution
import cartography.intel.gcp.cloudrun.job as cloudrun_job
import cartography.intel.gcp.cloudrun.revision as cloudrun_revision
import cartography.intel.gcp.cloudrun.service as cloudrun_service
from tests.data.gcp.cloudrun import MOCK_EXECUTIONS
from tests.data.gcp.cloudrun import MOCK_JOBS
from tests.data.gcp.cloudrun import MOCK_REVISIONS
from tests.data.gcp.cloudrun import MOCK_SERVICES
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
