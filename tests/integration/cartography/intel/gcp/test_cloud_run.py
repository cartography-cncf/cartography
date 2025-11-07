from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.cloud_run_domain_mapping as cloud_run_domain_mapping
import cartography.intel.gcp.cloud_run_execution as cloud_run_execution
import cartography.intel.gcp.cloud_run_job as cloud_run_job
import cartography.intel.gcp.cloud_run_locations as cloud_run_locations
import cartography.intel.gcp.cloud_run_revision as cloud_run_revision
import cartography.intel.gcp.cloud_run_service as cloud_run_service
from tests.data.gcp.cloud_run import MOCK_DOMAIN_MAPPINGS
from tests.data.gcp.cloud_run import MOCK_EXECUTIONS
from tests.data.gcp.cloud_run import MOCK_JOBS
from tests.data.gcp.cloud_run import MOCK_LOCATIONS
from tests.data.gcp.cloud_run import MOCK_REVISIONS
from tests.data.gcp.cloud_run import MOCK_SERVICES_LOC1
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"
TEST_SERVICE_NAME = "carto-test-service"
TEST_SERVICE_ID = (
    f"projects/{TEST_PROJECT_ID}/locations/us-central1/services/{TEST_SERVICE_NAME}"
)
TEST_REVISION_ID = f"{TEST_SERVICE_ID}/revisions/carto-test-service-00001-abc"
TEST_JOB_ID = f"projects/{TEST_PROJECT_ID}/locations/us-central1/jobs/carto-test-job"
TEST_EXECUTION_ID = f"{TEST_JOB_ID}/executions/carto-test-job-xyz"
TEST_DOMAIN_ID = (
    f"projects/{TEST_PROJECT_ID}/locations/us-central1/domainmappings/carto.example.com"
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
        sa_email="test-sa@test-project.iam.gserviceaccount.com",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (img:GCPGCRImage {id: $img_id}) SET img.lastupdated = $tag",
        img_id="gcr.io/test-project/hello@sha256:12345",
        tag=TEST_UPDATE_TAG,
    )


@patch("cartography.intel.gcp.cloud_run_domain_mapping.get_cloud_run_domain_mappings")
@patch("cartography.intel.gcp.cloud_run_execution.get_cloud_run_executions")
@patch("cartography.intel.gcp.cloud_run_revision.get_cloud_run_revisions")
@patch("cartography.intel.gcp.cloud_run_job.get_cloud_run_jobs")
@patch("cartography.intel.gcp.cloud_run_service.get_cloud_run_services")
@patch("cartography.intel.gcp.cloud_run_locations.get_cloud_run_locations")
def test_sync_cloud_run_modules(
    mock_get_locs,
    mock_get_svcs,
    mock_get_jobs,
    mock_get_revs,
    mock_get_execs,
    mock_get_domains,
    neo4j_session,
):
    """
    Test the sync functions for the refactored Cloud Run modules.
    This test simulates the behavior of the main gcp/__init__.py file.
    """
    # Arrange: Mock all 6 API calls
    mock_get_locs.return_value = MOCK_LOCATIONS
    mock_get_svcs.side_effect = [MOCK_SERVICES_LOC1, []]
    mock_get_jobs.side_effect = [MOCK_JOBS, []]
    mock_get_domains.side_effect = [MOCK_DOMAIN_MAPPINGS, []]
    mock_get_revs.return_value = MOCK_REVISIONS
    mock_get_execs.return_value = MOCK_EXECUTIONS

    # Arrange: Create prerequisite nodes
    _create_prerequisite_nodes(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    # Create mock clients for v1 and v2
    mock_run_client_v1 = MagicMock()
    mock_run_client_v2 = MagicMock()

    # Act: Call all 5 sync functions
    locations = cloud_run_locations.get_cloud_run_locations(
        mock_run_client_v1, TEST_PROJECT_ID
    )

    services_raw = cloud_run_service.sync_cloud_run_services(
        neo4j_session,
        mock_run_client_v2,
        locations,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    jobs_raw = cloud_run_job.sync_cloud_run_jobs(
        neo4j_session,
        mock_run_client_v2,
        locations,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    cloud_run_domain_mapping.sync_cloud_run_domain_mappings(
        neo4j_session,
        mock_run_client_v1,
        locations,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    cloud_run_revision.sync_cloud_run_revisions(
        neo4j_session,
        mock_run_client_v2,
        services_raw,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    cloud_run_execution.sync_cloud_run_executions(
        neo4j_session,
        mock_run_client_v2,
        jobs_raw,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: Check all 5 new node types
    assert check_nodes(neo4j_session, "GCPCloudRunService", ["id"]) == {
        (TEST_SERVICE_ID,)
    }
    assert check_nodes(neo4j_session, "GCPCloudRunRevision", ["id"]) == {
        (TEST_REVISION_ID,)
    }
    assert check_nodes(neo4j_session, "GCPCloudRunJob", ["id"]) == {(TEST_JOB_ID,)}
    assert check_nodes(neo4j_session, "GCPCloudRunExecution", ["id"]) == {
        (TEST_EXECUTION_ID,)
    }
    assert check_nodes(neo4j_session, "GCPCloudRunDomainMapping", ["id"]) == {
        (TEST_DOMAIN_ID,)
    }

    # Assert: Check all 12 relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPCloudRunService",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_SERVICE_ID)}

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPCloudRunRevision",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_REVISION_ID)}

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPCloudRunJob",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_JOB_ID)}

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPCloudRunExecution",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_EXECUTION_ID)}

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPCloudRunDomainMapping",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_DOMAIN_ID)}

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
    ) == {(TEST_JOB_ID, TEST_EXECUTION_ID)}

    assert check_rels(
        neo4j_session,
        "GCPCloudRunDomainMapping",
        "id",
        "GCPCloudRunService",
        "name",
        "POINTS_TO_SERVICE",
    ) == {(TEST_DOMAIN_ID, TEST_SERVICE_NAME)}

    assert check_rels(
        neo4j_session,
        "GCPCloudRunRevision",
        "id",
        "GCPServiceAccount",
        "email",
        "USES_SERVICE_ACCOUNT",
    ) == {(TEST_REVISION_ID, "test-sa@test-project.iam.gserviceaccount.com")}

    assert check_rels(
        neo4j_session,
        "GCPCloudRunJob",
        "id",
        "GCPServiceAccount",
        "email",
        "USES_SERVICE_ACCOUNT",
    ) == {(TEST_JOB_ID, "test-sa@test-project.iam.gserviceaccount.com")}

    assert check_rels(
        neo4j_session,
        "GCPCloudRunRevision",
        "id",
        "GCPGCRImage",
        "id",
        "USES_IMAGE",
    ) == {(TEST_REVISION_ID, "gcr.io/test-project/hello@sha256:12345")}

    assert check_rels(
        neo4j_session,
        "GCPCloudRunJob",
        "id",
        "GCPGCRImage",
        "id",
        "USES_IMAGE",
    ) == {(TEST_JOB_ID, "gcr.io/test-project/hello@sha256:12345")}
