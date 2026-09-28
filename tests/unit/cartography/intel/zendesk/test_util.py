from typing import cast
from unittest.mock import MagicMock

import pytest
import requests
from requests.adapters import HTTPAdapter

from cartography.intel.zendesk.util import configure_session
from cartography.intel.zendesk.util import get_paginated


def _response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_configure_session_mounts_bounded_get_retries() -> None:
    with requests.Session() as session:
        configure_session(session)
        retries = cast(
            HTTPAdapter, session.get_adapter("https://acme.zendesk.com")
        ).max_retries

        assert retries.total == 4
        assert retries.allowed_methods == frozenset({"GET"})
        assert {429, 500, 599} <= set(retries.status_forcelist)
        assert retries.respect_retry_after_header is True


@pytest.mark.parametrize(  # type: ignore[misc]
    "links",
    [
        {},
        {"next": 123},
    ],
)
def test_get_paginated_rejects_unusable_next_url(links: dict) -> None:
    # Arrange
    session = MagicMock(spec=requests.Session)
    session.get.return_value = _response(
        {
            "users": [{"id": 1}],
            "meta": {"has_more": True},
            "links": links,
        }
    )

    # Act and assert
    with pytest.raises(ValueError, match="usable next-page URL"):
        get_paginated(session, "acme", "users", "users", {})
