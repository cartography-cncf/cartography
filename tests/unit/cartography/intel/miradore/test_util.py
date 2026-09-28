import traceback
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from threading import Thread
from unittest.mock import Mock

import pytest
import requests
from requests.adapters import HTTPAdapter

from cartography.intel.miradore.util import as_list
from cartography.intel.miradore.util import create_miradore_api_session
from cartography.intel.miradore.util import get_nested
from cartography.intel.miradore.util import get_paginated_miradore_items
from cartography.intel.miradore.util import parse_bool
from cartography.intel.miradore.util import parse_datetime
from cartography.intel.miradore.util import parse_int
from cartography.intel.miradore.util import required_int_id
from cartography.intel.miradore.util import scoped_id

_BASE_URI = "https://online.miradore.com"
_SITE_NAME = "simpsoncorp"
_API_KEY = "1_AaDf234sdf8!4"


def _xml_response(items: str, count: int) -> Mock:
    return Mock(
        ok=True,
        status_code=200,
        text=f'<Content><Items count="{count}">{items}</Items></Content>',
    )


def _device_element(device_id: int) -> str:
    return f"<Device><ID>{device_id}</ID></Device>"


def test_get_paginated_miradore_items_stops_on_a_short_page() -> None:
    session = Mock()
    session.get.side_effect = [
        _xml_response("".join(_device_element(i) for i in range(2)), 2),
        _xml_response(_device_element(2), 1),
    ]

    results = get_paginated_miradore_items(
        session,
        _BASE_URI,
        _SITE_NAME,
        _API_KEY,
        "Device",
        "ID",
        page_size=2,
    )

    assert [item["ID"] for item in results] == ["0", "1", "2"]
    assert session.get.call_count == 2
    assert (
        session.get.call_args_list[0].args[0]
        == "https://online.miradore.com/simpsoncorp/API/Device"
    )
    assert session.get.call_args_list[0].kwargs["params"]["options"] == (
        "rows=2,page=1,dateformat=yyyy-MM-dd HH:mm:ss"
    )
    assert session.get.call_args_list[1].kwargs["params"]["options"] == (
        "rows=2,page=2,dateformat=yyyy-MM-dd HH:mm:ss"
    )


def test_get_paginated_miradore_items_passes_the_api_key_out_of_band() -> None:
    """The auth key is a query parameter, so it must never be baked into the URI."""
    session = Mock()
    session.get.return_value = _xml_response(_device_element(1), 1)

    get_paginated_miradore_items(
        session,
        _BASE_URI,
        _SITE_NAME,
        _API_KEY,
        "Device",
        "ID",
        page_size=100,
    )

    assert _API_KEY not in session.get.call_args.args[0]
    assert session.get.call_args.kwargs["params"]["auth"] == _API_KEY


def test_get_paginated_miradore_items_normalizes_a_single_item() -> None:
    session = Mock()
    session.get.return_value = _xml_response(_device_element(42), 1)

    results = get_paginated_miradore_items(
        session,
        _BASE_URI,
        _SITE_NAME,
        _API_KEY,
        "Device",
        "ID",
        page_size=100,
    )

    assert results == [{"ID": "42"}]


def test_get_paginated_miradore_items_handles_an_empty_result() -> None:
    session = Mock()
    session.get.return_value = _xml_response("", 0)

    results = get_paginated_miradore_items(
        session,
        _BASE_URI,
        _SITE_NAME,
        _API_KEY,
        "Device",
        "ID",
        page_size=100,
    )

    assert results == []


def test_get_paginated_miradore_items_never_discloses_the_api_key_on_an_error() -> None:
    """API v1 puts the key in the query string, and the sync runner logs exceptions.

    `requests`' own `raise_for_status()` embeds the full URL, key included, in the
    exception message, so an error response must be reported without it.
    """
    session = Mock()
    error_response = Mock(
        ok=False,
        status_code=401,
        url=f"https://online.miradore.com/simpsoncorp/API/Device?auth={_API_KEY}",
    )
    session.get.return_value = error_response

    with pytest.raises(requests.HTTPError) as excinfo:
        get_paginated_miradore_items(
            session,
            _BASE_URI,
            _SITE_NAME,
            _API_KEY,
            "Device",
            "ID",
            page_size=100,
        )

    assert _API_KEY not in str(excinfo.value)
    assert _API_KEY not in repr(excinfo.value)
    # The status and the key-free request path still make the failure diagnosable.
    assert "401" in str(excinfo.value)
    assert "https://online.miradore.com/simpsoncorp/API/Device" in str(excinfo.value)
    # Attaching the response would let a caller reach `response.url` and leak the key.
    assert excinfo.value.response is None


class _AlwaysUnavailableHandler(BaseHTTPRequestHandler):
    """Always answers 503, which the retry policy retries until it gives up."""

    def do_GET(self) -> None:
        self.send_response(503)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        pass


def test_get_paginated_miradore_items_never_discloses_the_api_key_on_exhausted_retries(
    mocker,
) -> None:
    """An exhausted retry raises out of `Session.get` before any status check runs.

    `RetryError` carries the prepared URL, so this goes through the real retry adapter
    rather than a mocked session: nothing else proves that path is sanitized.
    """
    server = ThreadingHTTPServer(("127.0.0.1", 0), _AlwaysUnavailableHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    session = create_miradore_api_session()
    # The session mounts the retry adapter on https://; the local server is http://.
    session.mount("http://", session.adapters["https://"])
    mocker.patch("urllib3.util.retry.time.sleep")

    try:
        with pytest.raises(requests.exceptions.RequestException) as excinfo:
            get_paginated_miradore_items(
                session,
                f"http://127.0.0.1:{server.server_port}",
                _SITE_NAME,
                _API_KEY,
                "Device",
                "ID",
                page_size=100,
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    # The retry adapter really did give up, rather than the request failing some other way.
    assert "RetryError" in str(excinfo.value)
    assert _API_KEY not in str(excinfo.value)
    assert _API_KEY not in repr(excinfo.value)
    # `from None` must keep the original message, which carries the key, out of the
    # traceback the sync runner logs.
    rendered = "".join(
        traceback.format_exception(
            type(excinfo.value),
            excinfo.value,
            excinfo.value.__traceback__,
        )
    )
    assert _API_KEY not in rendered


def test_get_paginated_miradore_items_rejects_an_unexpected_document() -> None:
    """A sign-in or error page served with HTTP 200 must not look like an empty page.

    Returning no rows would let the cleanup that follows delete the resource's nodes.
    """
    session = Mock()
    session.get.return_value = Mock(
        ok=True,
        status_code=200,
        text="<html><body>Please sign in</body></html>",
    )

    with pytest.raises(ValueError, match="without the expected <Content><Items>"):
        get_paginated_miradore_items(
            session,
            _BASE_URI,
            _SITE_NAME,
            _API_KEY,
            "Device",
            "ID",
            page_size=100,
        )


def test_get_paginated_miradore_items_accepts_a_genuinely_empty_page() -> None:
    """The real API answers a query with no matches with a self-closing element."""
    session = Mock()
    session.get.return_value = Mock(
        ok=True,
        status_code=200,
        text='<Content><Items count="0" /></Content>',
    )

    assert (
        get_paginated_miradore_items(
            session,
            _BASE_URI,
            _SITE_NAME,
            _API_KEY,
            "Device",
            "ID",
            page_size=100,
        )
        == []
    )


def test_required_int_id_parses_the_identifier() -> None:
    assert required_int_id({"ID": "1001"}, "Device") == 1001


def test_required_int_id_raises_when_the_attribute_is_absent() -> None:
    """A required field must fail loudly rather than yield a null graph identity."""
    with pytest.raises(KeyError):
        required_int_id({"Name": "no id here"}, "Device")


def test_required_int_id_raises_when_the_identifier_is_not_an_integer() -> None:
    with pytest.raises(ValueError, match="Device whose ID is not an integer"):
        required_int_id({"ID": "not-a-number"}, "Device")


def test_create_miradore_api_session_retries_transient_failures() -> None:
    """A blip on one page must not abort the whole sync; every call is an idempotent GET."""
    session = create_miradore_api_session()

    adapter = session.get_adapter("https://online.miradore.com")
    assert isinstance(adapter, HTTPAdapter)
    retries = adapter.max_retries
    assert retries.total == 5
    assert 429 in retries.status_forcelist
    assert 503 in retries.status_forcelist
    assert retries.allowed_methods == ["GET"]


def test_scoped_id_prefixes_the_site_name() -> None:
    assert scoped_id("simpsoncorp", 1001) == "simpsoncorp/1001"
    assert scoped_id("simpsoncorp", "engineering") == "simpsoncorp/engineering"


def test_scoped_id_is_unique_across_tenants() -> None:
    """Miradore numbers items per tenant, so the same raw ID must not collide."""
    assert scoped_id("simpsoncorp", 1001) != scoped_id("southpark", 1001)


def test_scoped_id_passes_through_a_missing_id() -> None:
    """A null foreign key must stay null so the relationship simply does not match."""
    assert scoped_id("simpsoncorp", None) is None


def test_as_list_normalizes_miradore_list_attributes() -> None:
    assert as_list(None) == []
    assert as_list({"Name": "engineering"}) == [{"Name": "engineering"}]
    assert as_list([{"Name": "a"}, {"Name": "b"}]) == [{"Name": "a"}, {"Name": "b"}]


def test_get_nested_returns_none_for_missing_paths() -> None:
    assert get_nested({"User": {"ID": "1"}}, "User", "ID") == "1"
    assert get_nested({"User": {"ID": "1"}}, "User", "Email") is None
    assert get_nested({}, "User", "ID") is None


def test_parse_datetime() -> None:
    assert parse_datetime("2026-08-01 07:45:10") == datetime(2026, 8, 1, 7, 45, 10)
    assert parse_datetime("") is None
    assert parse_datetime(None) is None
    assert parse_datetime("01.08.2026 07:45:10") is None


def test_parse_int() -> None:
    assert parse_int("1001") == 1001
    assert parse_int(1001) == 1001
    assert parse_int("") is None
    assert parse_int(None) is None
    assert parse_int("not-a-number") is None


def test_parse_bool() -> None:
    assert parse_bool("true") is True
    assert parse_bool("False") is False
    assert parse_bool(True) is True
    assert parse_bool("Yes") is True
    assert parse_bool("Unknown") is None
    assert parse_bool(None) is None
