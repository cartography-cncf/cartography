from unittest.mock import MagicMock

from google.cloud.bigquery_connection_v1.types import Connection

import cartography.intel.gcp as gcp_intel
from cartography.intel.gcp.bigquery_connection import _connection_to_dict


def test_get_cached_reuses_factory_result():
    client_cache = {}
    client = MagicMock()
    factory = MagicMock(return_value=client)

    first = gcp_intel._get_cached(client_cache, ("svc", "v1"), factory)
    second = gcp_intel._get_cached(client_cache, ("svc", "v1"), factory)

    assert first is second is client
    factory.assert_called_once()


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
