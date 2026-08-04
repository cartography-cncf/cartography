from unittest.mock import MagicMock

import pytest
import requests

from cartography.intel.supabase.util import epoch_ms_to_datetime
from cartography.intel.supabase.util import get_json
from cartography.intel.supabase.util import iso_to_datetime
from cartography.intel.supabase.util import TOLERATED_STATUSES

# The real body a free-tier organization gets back from /vanity-subdomain and
# /custom-hostname. Captured from the live Management API.
ENTITLEMENT_REQUIRED_BODY = {
    "message": "This feature requires the Pro, Team, or Enterprise organization plan.",
    "error": {
        "code": "entitlement_required",
        "feature": "vanity_subdomain",
        "upgrade_url": "https://supabase.com/dashboard/org/anorg/billing",
    },
}


def _session(status_code, json_body=None, raise_on_json=False):
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    if raise_on_json:
        response.json.side_effect = ValueError("not json")
    else:
        response.json.return_value = json_body
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"{status_code} Client Error",
            response=response,
        )
    else:
        response.raise_for_status.return_value = None

    api_session = MagicMock(spec=requests.Session)
    api_session.get.return_value = response
    return api_session


def test_get_json_returns_body_on_success():
    api_session = _session(200, {"enabled": True})

    assert get_json(api_session, "https://api.supabase.com/v1/x") == {"enabled": True}


@pytest.mark.parametrize("status_code", TOLERATED_STATUSES)
def test_get_json_tolerates_configured_statuses(status_code):
    api_session = _session(status_code, {})

    assert (
        get_json(
            api_session,
            "https://api.supabase.com/v1/x",
            tolerate=TOLERATED_STATUSES,
        )
        is None
    )


def test_get_json_tolerates_entitlement_required_400():
    """
    Plan-gated endpoints answer 400 with an entitlement_required error code rather
    than 402 or 403, so that specific 400 must be treated as "feature unavailable".
    """
    api_session = _session(400, ENTITLEMENT_REQUIRED_BODY)

    assert (
        get_json(
            api_session,
            "https://api.supabase.com/v1/x",
            tolerate=TOLERATED_STATUSES,
        )
        is None
    )


def test_get_json_raises_on_ordinary_400():
    """
    A 400 that is not an entitlement error is a real bug and must stay loud.
    """
    api_session = _session(400, {"message": "invalid project ref"})

    with pytest.raises(requests.exceptions.HTTPError):
        get_json(
            api_session,
            "https://api.supabase.com/v1/x",
            tolerate=TOLERATED_STATUSES,
        )


def test_get_json_raises_on_400_with_unparseable_body():
    api_session = _session(400, raise_on_json=True)

    with pytest.raises(requests.exceptions.HTTPError):
        get_json(
            api_session,
            "https://api.supabase.com/v1/x",
            tolerate=TOLERATED_STATUSES,
        )


def test_get_json_raises_when_nothing_is_tolerated():
    """
    Endpoints that are not plan-gated pass no tolerate list, so even a 404 raises.
    """
    api_session = _session(404, {})

    with pytest.raises(requests.exceptions.HTTPError):
        get_json(api_session, "https://api.supabase.com/v1/x")


def test_get_json_raises_on_server_error():
    api_session = _session(500, {})

    with pytest.raises(requests.exceptions.HTTPError):
        get_json(
            api_session,
            "https://api.supabase.com/v1/x",
            tolerate=TOLERATED_STATUSES,
        )


def test_iso_to_datetime():
    parsed = iso_to_datetime("2026-07-28T16:37:25.429581Z")

    assert (parsed.year, parsed.month, parsed.day) == (2026, 7, 28)
    assert parsed.tzinfo is not None


@pytest.mark.parametrize("empty", [None, ""])
def test_iso_to_datetime_handles_empty(empty):
    assert iso_to_datetime(empty) is None


def test_epoch_ms_to_datetime():
    # The functions endpoints return epoch milliseconds, unlike the rest of the API.
    parsed = epoch_ms_to_datetime(1782000000000)

    assert (parsed.year, parsed.month, parsed.day) == (2026, 6, 21)
    assert parsed.tzinfo is not None


def test_epoch_ms_to_datetime_handles_none():
    assert epoch_ms_to_datetime(None) is None


def test_epoch_ms_to_datetime_handles_zero():
    # 0 is a real timestamp (the epoch), not a missing value.
    assert epoch_ms_to_datetime(0) is not None
