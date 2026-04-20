from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.cloudrun.execution import get_executions
from cartography.intel.gcp.cloudrun.revision import get_revisions


def test_get_revisions_reuses_shared_gapic_client():
    shared_client = MagicMock(name="shared-run-revisions-client")
    services_raw = [{"name": "service-1"}, {"name": "service-2"}]
    seen_clients: list[object] = []

    def _mock_get_revisions_for_service(client, service_name):
        seen_clients.append(client)
        return [{"name": f"{service_name}/revision"}]

    with patch(
        "cartography.intel.gcp.cloudrun.revision._get_revisions_for_service",
        side_effect=_mock_get_revisions_for_service,
    ):
        revisions = get_revisions(
            shared_client,
            "test-project",
            services_raw=services_raw,
            max_workers=4,
        )

    assert revisions == [
        {"name": "service-1/revision"},
        {"name": "service-2/revision"},
    ]
    assert seen_clients
    assert all(client is shared_client for client in seen_clients)


def test_get_revisions_can_fetch_services_when_not_prefetched():
    shared_client = MagicMock(name="shared-run-revisions-client")
    services_client = MagicMock(name="shared-run-services-client")

    with (
        patch(
            "cartography.intel.gcp.cloudrun.revision.discover_cloud_run_locations",
            return_value={"projects/test-project/locations/us-central1"},
        ),
        patch(
            "cartography.intel.gcp.cloudrun.revision.get_services",
            return_value=[{"name": "service-1"}],
        ) as mock_get_services,
        patch(
            "cartography.intel.gcp.cloudrun.revision._get_revisions_for_service",
            return_value=[{"name": "service-1/revision"}],
        ),
    ):
        revisions = get_revisions(
            shared_client,
            "test-project",
            services_client=services_client,
            credentials=MagicMock(),
        )

    assert revisions == [{"name": "service-1/revision"}]
    mock_get_services.assert_called_once()


def test_get_executions_reuses_shared_gapic_client():
    shared_client = MagicMock(name="shared-run-executions-client")
    jobs_raw = [{"name": "job-1"}, {"name": "job-2"}]
    seen_clients: list[object] = []

    def _mock_get_executions_for_job(client, job_name):
        seen_clients.append(client)
        return [{"name": f"{job_name}/execution"}]

    with patch(
        "cartography.intel.gcp.cloudrun.execution._get_executions_for_job",
        side_effect=_mock_get_executions_for_job,
    ):
        executions = get_executions(
            shared_client,
            "test-project",
            jobs_raw=jobs_raw,
            max_workers=4,
        )

    assert executions == [
        {"name": "job-1/execution"},
        {"name": "job-2/execution"},
    ]
    assert seen_clients
    assert all(client is shared_client for client in seen_clients)


def test_get_executions_can_fetch_jobs_when_not_prefetched():
    shared_client = MagicMock(name="shared-run-executions-client")
    jobs_client = MagicMock(name="shared-run-jobs-client")

    with (
        patch(
            "cartography.intel.gcp.cloudrun.execution.get_jobs",
            return_value=[{"name": "job-1"}],
        ) as mock_get_jobs,
        patch(
            "cartography.intel.gcp.cloudrun.execution._get_executions_for_job",
            return_value=[{"name": "job-1/execution"}],
        ),
    ):
        executions = get_executions(
            shared_client,
            "test-project",
            jobs_client=jobs_client,
            credentials=MagicMock(),
        )

    assert executions == [{"name": "job-1/execution"}]
    mock_get_jobs.assert_called_once()
