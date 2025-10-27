from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.cloud_run as cloud_run
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


def _create_prerequisite_nodes(neo4j_session):
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


@patch("cartography.intel.gcp.cloud_run.get_cloud_run_domain_mappings")
@patch("cartography.intel.gcp.cloud_run.get_cloud_run_executions")
@patch("cartography.intel.gcp.cloud_run.get_cloud_run_jobs")
@patch("cartography.intel.gcp.cloud_run.get_cloud_run_revisions")
@patch("cartography.intel.gcp.cloud_run.get_cloud_run_services")
@patch("cartography.intel.gcp.cloud_run.get_cloud_run_locations")
def test_sync_cloud_run(
    mock_get_locs,
    mock_get_svcs,
    mock_get_revs,
    mock_get_jobs,
    mock_get_execs,
    mock_get_domains,
    neo4j_session,
):
    mock_get_locs.return_value = MOCK_LOCATIONS
    mock_get_svcs.side_effect = [MOCK_SERVICES_LOC1, []]
    mock_get_jobs.side_effect = [MOCK_JOBS, []]
    mock_get_domains.side_effect = [MOCK_DOMAIN_MAPPINGS, []]
    mock_get_revs.return_value = MOCK_REVISIONS
    mock_get_execs.return_value = MOCK_EXECUTIONS

    _create_prerequisite_nodes(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "project_id": TEST_PROJECT_ID,
    }

    mock_run_client_v2 = MagicMock()
    mock_run_client_v1 = MagicMock()

    cloud_run.sync(
        neo4j_session,
        mock_run_client_v2,
        mock_run_client_v1,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_nodes(neo4j_session, "GCPCloudRunService", ["id"]) == {
        ("projects/test-project/locations/us-central1/services/carto-test-service",)
    }
    assert check_nodes(neo4j_session, "GCPCloudRunRevision", ["id"]) == {
        (
            "projects/test-project/locations/us-central1/services/carto-test-service/revisions/carto-test-service-00001-abc",
        )
    }
    assert check_nodes(neo4j_session, "GCPCloudRunJob", ["id"]) == {
        ("projects/test-project/locations/us-central1/jobs/carto-test-job",)
    }
    assert check_nodes(neo4j_session, "GCPCloudRunExecution", ["id"]) == {
        (
            "projects/test-project/locations/us-central1/jobs/carto-test-job/executions/carto-test-job-xyz",
        )
    }
    assert check_nodes(neo4j_session, "GCPCloudRunDomainMapping", ["id"]) == {
        (
            "projects/test-project/locations/us-central1/domainmappings/carto.example.com",
        )
    }

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPCloudRunService",
        "id",
        "RESOURCE",
    ) == {
        (
            "test-project",
            "projects/test-project/locations/us-central1/services/carto-test-service",
        )
    }

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPCloudRunRevision",
        "id",
        "RESOURCE",
    ) == {
        (
            "test-project",
            "projects/test-project/locations/us-central1/services/carto-test-service/revisions/carto-test-service-00001-abc",
        )
    }

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPCloudRunJob",
        "id",
        "RESOURCE",
    ) == {
        (
            "test-project",
            "projects/test-project/locations/us-central1/jobs/carto-test-job",
        )
    }

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPCloudRunExecution",
        "id",
        "RESOURCE",
    ) == {
        (
            "test-project",
            "projects/test-project/locations/us-central1/jobs/carto-test-job/executions/carto-test-job-xyz",
        )
    }

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPCloudRunDomainMapping",
        "id",
        "RESOURCE",
    ) == {
        (
            "test-project",
            "projects/test-project/locations/us-central1/domainmappings/carto.example.com",
        )
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunService",
        "id",
        "GCPCloudRunRevision",
        "id",
        "HAS_REVISION",
    ) == {
        (
            "projects/test-project/locations/us-central1/services/carto-test-service",
            "projects/test-project/locations/us-central1/services/carto-test-service/revisions/carto-test-service-00001-abc",
        )
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunJob",
        "id",
        "GCPCloudRunExecution",
        "id",
        "HAS_EXECUTION",
    ) == {
        (
            "projects/test-project/locations/us-central1/jobs/carto-test-job",
            "projects/test-project/locations/us-central1/jobs/carto-test-job/executions/carto-test-job-xyz",
        )
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunDomainMapping",
        "id",
        "GCPCloudRunService",
        "name",
        "POINTS_TO_SERVICE",
    ) == {
        (
            "projects/test-project/locations/us-central1/domainmappings/carto.example.com",
            "carto-test-service",
        )
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunRevision",
        "id",
        "GCPServiceAccount",
        "email",
        "USES_SERVICE_ACCOUNT",
    ) == {
        (
            "projects/test-project/locations/us-central1/services/carto-test-service/revisions/carto-test-service-00001-abc",
            "test-sa@test-project.iam.gserviceaccount.com",
        )
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunJob",
        "id",
        "GCPServiceAccount",
        "email",
        "USES_SERVICE_ACCOUNT",
    ) == {
        (
            "projects/test-project/locations/us-central1/jobs/carto-test-job",
            "test-sa@test-project.iam.gserviceaccount.com",
        )
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunRevision",
        "id",
        "GCPGCRImage",
        "id",
        "USES_IMAGE",
    ) == {
        (
            "projects/test-project/locations/us-central1/services/carto-test-service/revisions/carto-test-service-00001-abc",
            "gcr.io/test-project/hello@sha256:12345",
        )
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudRunJob",
        "id",
        "GCPGCRImage",
        "id",
        "USES_IMAGE",
    ) == {
        (
            "projects/test-project/locations/us-central1/jobs/carto-test-job",
            "gcr.io/test-project/hello@sha256:12345",
        )
    }
