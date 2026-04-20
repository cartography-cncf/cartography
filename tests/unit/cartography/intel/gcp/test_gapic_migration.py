from unittest.mock import MagicMock
from unittest.mock import patch

from google.cloud.bigquery_connection_v1.types import Connection

import cartography.intel.gcp as gcp_intel
from cartography.intel.gcp.bigquery_connection import _connection_to_dict
from cartography.intel.gcp.clients import CloudRunClients


def test_cached_cloud_run_clients_reused():
    client_cache = {}
    credentials = MagicMock()
    clients = CloudRunClients(
        services=MagicMock(),
        jobs=MagicMock(),
        revisions=MagicMock(),
        executions=MagicMock(),
    )

    with patch(
        "cartography.intel.gcp.build_cloud_run_clients",
        return_value=clients,
    ) as mock_build_cloud_run_clients:
        first = gcp_intel._get_cached_cloud_run_clients(client_cache, credentials)
        second = gcp_intel._get_cached_cloud_run_clients(client_cache, credentials)

    assert first is second is clients
    mock_build_cloud_run_clients.assert_called_once_with(credentials=credentials)


def test_cached_bigquery_gapic_client_reused():
    client_cache = {}
    credentials = MagicMock()
    client = MagicMock()

    with patch(
        "cartography.intel.gcp.build_bigquery_client",
        return_value=client,
    ) as mock_build_bigquery_client:
        first = gcp_intel._get_cached_bigquery_gapic_client(client_cache, credentials)
        second = gcp_intel._get_cached_bigquery_gapic_client(client_cache, credentials)

    assert first is second is client
    mock_build_bigquery_client.assert_called_once_with(credentials=credentials)


def test_cached_bigquery_connection_gapic_client_reused():
    client_cache = {}
    credentials = MagicMock()
    client = MagicMock()

    with patch(
        "cartography.intel.gcp.build_bigquery_connection_client",
        return_value=client,
    ) as mock_build_bigquery_connection_client:
        first = gcp_intel._get_cached_bigquery_connection_gapic_client(
            client_cache,
            credentials,
        )
        second = gcp_intel._get_cached_bigquery_connection_gapic_client(
            client_cache,
            credentials,
        )

    assert first is second is client
    mock_build_bigquery_connection_client.assert_called_once_with(
        credentials=credentials
    )


def test_connection_to_dict_preserves_bigquery_connection_shape():
    connection = Connection(
        name="projects/test-project/locations/us/connections/my-cloud-sql-conn",
        friendly_name="My Cloud SQL Connection",
        description="Connection to Cloud SQL",
        creation_time=1640000000000,
        last_modified_time=1640100000000,
        has_credential=True,
        cloud_sql={"instance_id": "test-project:us-central1:my-instance"},
    )

    assert _connection_to_dict(connection) == {
        "name": "projects/test-project/locations/us/connections/my-cloud-sql-conn",
        "friendlyName": "My Cloud SQL Connection",
        "description": "Connection to Cloud SQL",
        "creationTime": "1640000000000",
        "lastModifiedTime": "1640100000000",
        "hasCredential": True,
        "cloudSql": {"instanceId": "test-project:us-central1:my-instance"},
    }
