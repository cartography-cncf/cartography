from unittest.mock import MagicMock

from google.api_core.exceptions import NotFound
from google.api_core.exceptions import PermissionDenied

from cartography.intel.gcp.bigquery_connection import get_bigquery_connections
from cartography.intel.gcp.cloudrun.job import get_jobs
from cartography.intel.gcp.cloudrun.service import get_services


def _raise_on_iteration(exc):
    def _iterator():
        raise exc
        yield None

    return _iterator()


def test_get_services_returns_none_when_all_locations_denied_during_iteration():
    client = MagicMock()
    client.list_services.side_effect = lambda parent: _raise_on_iteration(
        PermissionDenied("denied")
    )

    result = get_services(
        client,
        "test-project",
        locations={"projects/test-project/locations/us-central1"},
    )

    assert result is None


def test_get_jobs_returns_none_when_all_locations_denied_during_iteration():
    client = MagicMock()
    client.list_jobs.side_effect = lambda parent: _raise_on_iteration(
        PermissionDenied("denied")
    )

    result = get_jobs(
        client,
        "test-project",
        locations={"projects/test-project/locations/us-central1"},
    )

    assert result is None


def test_get_bigquery_connections_returns_none_when_all_locations_denied():
    client = MagicMock()
    client.list_connections.side_effect = lambda parent: _raise_on_iteration(
        PermissionDenied("denied")
    )

    result = get_bigquery_connections(client, "test-project")

    assert result is None


def test_get_bigquery_connections_skips_missing_location():
    client = MagicMock()

    def _list_connections(parent):
        if parent.endswith("/us"):
            return _raise_on_iteration(NotFound("missing"))
        return iter([])

    client.list_connections.side_effect = _list_connections

    result = get_bigquery_connections(client, "test-project")

    assert result == []
