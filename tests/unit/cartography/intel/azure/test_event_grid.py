from unittest.mock import MagicMock

import pytest
from azure.core.exceptions import HttpResponseError

from cartography.intel.azure.event_grid import get_event_grid_topics


def _error(code: str) -> HttpResponseError:
    error = HttpResponseError(message=code)
    error.error = MagicMock(code=code)
    return error


def test_get_event_grid_topics_skips_disallowed_provider():
    credentials = MagicMock()
    with pytest.MonkeyPatch.context() as monkeypatch:
        client = MagicMock()
        client.topics.list_by_subscription.side_effect = _error("DisallowedProvider")
        monkeypatch.setattr(
            "cartography.intel.azure.event_grid.EventGridManagementClient",
            lambda credential, subscription_id: client,
        )

        assert get_event_grid_topics(credentials, "subscription-id") is None


def test_get_event_grid_topics_reraises_unexpected_error():
    credentials = MagicMock()
    with pytest.MonkeyPatch.context() as monkeypatch:
        client = MagicMock()
        client.topics.list_by_subscription.side_effect = _error("Forbidden")
        monkeypatch.setattr(
            "cartography.intel.azure.event_grid.EventGridManagementClient",
            lambda credential, subscription_id: client,
        )

        with pytest.raises(HttpResponseError):
            get_event_grid_topics(credentials, "subscription-id")
