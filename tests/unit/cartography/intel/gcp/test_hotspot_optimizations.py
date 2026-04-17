from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp as gcp


def _make_discovery_client(name: str) -> MagicMock:
    client = MagicMock(name=name)
    client._client_name = name
    return client


@patch.object(gcp, "run_scoped_analysis_job")
@patch.object(gcp.cloudrun_execution, "sync_executions")
@patch.object(gcp.cloudrun_job, "sync_jobs")
@patch.object(gcp.cloudrun_revision, "sync_revisions")
@patch.object(gcp.cloudrun_service, "sync_services")
@patch.object(gcp.cloudrun_util, "discover_cloud_run_locations")
@patch.object(gcp.bigquery_routine, "sync_bigquery_routines")
@patch.object(gcp.bigquery_table, "sync_bigquery_tables")
@patch.object(gcp.bigquery_connection, "sync_bigquery_connections")
@patch.object(gcp.bigquery_dataset, "sync_bigquery_datasets")
@patch.object(gcp.artifact_registry, "sync")
@patch.object(gcp, "_services_enabled_on_project")
@patch.object(gcp, "build_client")
def test_sync_project_resources_reuses_clients_and_prefetched_data(
    mock_build_client,
    mock_services_enabled,
    mock_artifact_registry_sync,
    mock_sync_bigquery_datasets,
    mock_sync_bigquery_connections,
    mock_sync_bigquery_tables,
    mock_sync_bigquery_routines,
    mock_discover_cloud_run_locations,
    mock_sync_services,
    mock_sync_revisions,
    mock_sync_jobs,
    mock_sync_executions,
    mock_run_scoped_analysis_job,
):
    client_cache: dict[tuple[str, str], object] = {}
    common_job_parameters = {"UPDATE_TAG": 123456789}
    projects = [{"projectId": "project-a"}, {"projectId": "project-b"}]
    credentials = MagicMock()

    service_set = {
        gcp.service_names.artifact_registry,
        gcp.service_names.cloud_run,
        gcp.service_names.bigquery,
        gcp.service_names.bigquery_connection,
    }
    mock_services_enabled.side_effect = [service_set, service_set]
    mock_discover_cloud_run_locations.side_effect = [
        {"projects/project-a/locations/us-central1"},
        {"projects/project-b/locations/europe-west1"},
    ]
    mock_sync_services.side_effect = [
        [{"name": "projects/project-a/locations/us-central1/services/api"}],
        [{"name": "projects/project-b/locations/europe-west1/services/worker"}],
    ]
    mock_sync_jobs.side_effect = [
        [{"name": "projects/project-a/locations/us-central1/jobs/batch"}],
        [{"name": "projects/project-b/locations/europe-west1/jobs/etl"}],
    ]
    mock_sync_bigquery_datasets.side_effect = [
        [{"datasetReference": {"datasetId": "analytics"}, "location": "US"}],
        [{"datasetReference": {"datasetId": "warehouse"}, "location": "EU"}],
    ]

    clients = {
        ("serviceusage", "v1"): _make_discovery_client("serviceusage-v1"),
        ("artifactregistry", "v1"): _make_discovery_client("artifactregistry-v1"),
        ("run", "v2"): _make_discovery_client("run-v2"),
        ("bigquery", "v2"): _make_discovery_client("bigquery-v2"),
        ("bigqueryconnection", "v1"): _make_discovery_client("bigqueryconnection-v1"),
    }
    mock_build_client.side_effect = lambda service, version, credentials=None: clients[
        (service, version)
    ]

    gcp._sync_project_resources(
        neo4j_session=MagicMock(),
        projects=projects,
        gcp_update_tag=123456789,
        common_job_parameters=common_job_parameters,
        credentials=credentials,
        client_cache=client_cache,
        requested_syncs={
            "artifact_registry",
            "cloud_run",
            "bigquery",
            "bigquery_connection",
        },
    )

    assert mock_build_client.call_args_list == [
        call("serviceusage", "v1", credentials=credentials),
        call("artifactregistry", "v1", credentials=credentials),
        call("run", "v2", credentials=credentials),
        call("bigquery", "v2", credentials=credentials),
        call("bigqueryconnection", "v1", credentials=credentials),
    ]
    assert len(mock_build_client.call_args_list) == 5

    assert mock_sync_bigquery_connections.call_args_list[0].kwargs["datasets_raw"] == [
        {"datasetReference": {"datasetId": "analytics"}, "location": "US"}
    ]
    assert mock_sync_bigquery_connections.call_args_list[1].kwargs["datasets_raw"] == [
        {"datasetReference": {"datasetId": "warehouse"}, "location": "EU"}
    ]

    assert mock_sync_revisions.call_args_list[0].kwargs["services_raw"] == [
        {"name": "projects/project-a/locations/us-central1/services/api"}
    ]
    assert mock_sync_revisions.call_args_list[1].kwargs["services_raw"] == [
        {"name": "projects/project-b/locations/europe-west1/services/worker"}
    ]
    assert mock_sync_executions.call_args_list[0].kwargs["jobs_raw"] == [
        {"name": "projects/project-a/locations/us-central1/jobs/batch"}
    ]
    assert mock_sync_executions.call_args_list[1].kwargs["jobs_raw"] == [
        {"name": "projects/project-b/locations/europe-west1/jobs/etl"}
    ]

    assert "PROJECT_ID" not in common_job_parameters
    mock_artifact_registry_sync.assert_called()
    mock_sync_bigquery_tables.assert_called()
    mock_sync_bigquery_routines.assert_called()
    mock_run_scoped_analysis_job.assert_not_called()
