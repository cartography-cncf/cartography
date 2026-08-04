from datetime import datetime
from unittest.mock import Mock

from cartography.intel.miradore.util import as_list
from cartography.intel.miradore.util import get_nested
from cartography.intel.miradore.util import get_paginated_miradore_items
from cartography.intel.miradore.util import parse_bool
from cartography.intel.miradore.util import parse_datetime
from cartography.intel.miradore.util import parse_int
from cartography.intel.miradore.util import scoped_id

_BASE_URI = "https://online.miradore.com"
_SITE_NAME = "simpsoncorp"
_API_KEY = "1_AaDf234sdf8!4"


def _xml_response(items: str, count: int) -> Mock:
    response = Mock()
    response.text = f'<Content><Items count="{count}">{items}</Items></Content>'
    return response


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
