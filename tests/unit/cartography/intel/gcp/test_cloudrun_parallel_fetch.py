from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.cloudrun.execution import get_executions
from cartography.intel.gcp.cloudrun.revision import get_revisions


def test_get_revisions_falls_back_to_sequential_without_credentials():
    shared_client = MagicMock(name="shared-run-client")
    services_raw = [{"name": "service-1"}, {"name": "service-2"}]
    seen_clients: list[object] = []

    def _mock_get_revisions_for_service(client, service_name):
        seen_clients.append(client)
        return [{"name": f"{service_name}/revision"}]

    with (
        patch(
            "cartography.intel.gcp.cloudrun.revision._get_revisions_for_service",
            side_effect=_mock_get_revisions_for_service,
        ),
        patch(
            "cartography.intel.gcp.cloudrun.revision.build_client"
        ) as mock_build_client,
    ):
        revisions = get_revisions(
            shared_client,
            "test-project",
            services_raw=services_raw,
            max_workers=4,
            credentials=None,
        )

    assert revisions == [
        {"name": "service-1/revision"},
        {"name": "service-2/revision"},
    ]
    assert seen_clients == [shared_client, shared_client]
    mock_build_client.assert_not_called()


def test_get_revisions_uses_thread_local_clients_when_credentials_provided():
    shared_client = MagicMock(name="shared-run-client")
    credentials = MagicMock()
    services_raw = [{"name": "service-1"}, {"name": "service-2"}]
    seen_clients: list[object] = []

    def _mock_get_revisions_for_service(client, service_name):
        seen_clients.append(client)
        return [{"name": f"{service_name}/revision"}]

    with (
        patch(
            "cartography.intel.gcp.cloudrun.revision._get_revisions_for_service",
            side_effect=_mock_get_revisions_for_service,
        ),
        patch(
            "cartography.intel.gcp.cloudrun.revision.build_client",
            return_value=MagicMock(name="thread-run-client"),
        ) as mock_build_client,
    ):
        revisions = get_revisions(
            shared_client,
            "test-project",
            services_raw=services_raw,
            max_workers=4,
            credentials=credentials,
        )

    assert revisions == [
        {"name": "service-1/revision"},
        {"name": "service-2/revision"},
    ]
    assert seen_clients
    assert all(client is not shared_client for client in seen_clients)
    mock_build_client.assert_called()


def test_get_executions_falls_back_to_sequential_without_credentials():
    shared_client = MagicMock(name="shared-run-client")
    jobs_raw = [{"name": "job-1"}, {"name": "job-2"}]
    seen_clients: list[object] = []

    def _mock_get_executions_for_job(client, job_name):
        seen_clients.append(client)
        return [{"name": f"{job_name}/execution"}]

    with (
        patch(
            "cartography.intel.gcp.cloudrun.execution._get_executions_for_job",
            side_effect=_mock_get_executions_for_job,
        ),
        patch(
            "cartography.intel.gcp.cloudrun.execution.build_client"
        ) as mock_build_client,
    ):
        executions = get_executions(
            shared_client,
            "test-project",
            jobs_raw=jobs_raw,
            max_workers=4,
            credentials=None,
        )

    assert executions == [
        {"name": "job-1/execution"},
        {"name": "job-2/execution"},
    ]
    assert seen_clients == [shared_client, shared_client]
    mock_build_client.assert_not_called()


def test_get_executions_uses_thread_local_clients_when_credentials_provided():
    shared_client = MagicMock(name="shared-run-client")
    credentials = MagicMock()
    jobs_raw = [{"name": "job-1"}, {"name": "job-2"}]
    seen_clients: list[object] = []

    def _mock_get_executions_for_job(client, job_name):
        seen_clients.append(client)
        return [{"name": f"{job_name}/execution"}]

    with (
        patch(
            "cartography.intel.gcp.cloudrun.execution._get_executions_for_job",
            side_effect=_mock_get_executions_for_job,
        ),
        patch(
            "cartography.intel.gcp.cloudrun.execution.build_client",
            return_value=MagicMock(name="thread-run-client"),
        ) as mock_build_client,
    ):
        executions = get_executions(
            shared_client,
            "test-project",
            jobs_raw=jobs_raw,
            max_workers=4,
            credentials=credentials,
        )

    assert executions == [
        {"name": "job-1/execution"},
        {"name": "job-2/execution"},
    ]
    assert seen_clients
    assert all(client is not shared_client for client in seen_clients)
    mock_build_client.assert_called()
