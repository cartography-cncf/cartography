from typing import Any
from unittest import mock

import pytest
import requests

from cartography.intel.civo.util import fan_out_array_across_regions
from cartography.intel.civo.util import fan_out_paginated_across_regions
from cartography.intel.civo.util import get_json_array
from cartography.intel.civo.util import get_regions
from cartography.intel.civo.util import list_all_pages
from cartography.intel.civo.util import region_codes_for_feature
from cartography.intel.civo.util import require_non_empty
from tests.data.civo.sshkeys import SSH_KEYS_PAGE_1
from tests.data.civo.sshkeys import SSH_KEYS_PAGE_2


def _make_response(payload: Any) -> mock.MagicMock:
    resp = mock.MagicMock(spec=requests.Response)
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


def test_list_all_pages_walks_every_page() -> None:
    # Arrange: two pages, as reported by "pages": 2.
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _make_response(SSH_KEYS_PAGE_1),
        _make_response(SSH_KEYS_PAGE_2),
    ]

    # Act
    results = list_all_pages(session, "https://api.civo.com/v2/sshkeys")

    # Assert: items from both pages are combined, and the loop stopped there.
    assert results == SSH_KEYS_PAGE_1["items"] + SSH_KEYS_PAGE_2["items"]
    assert session.get.call_count == 2
    assert session.get.call_args_list[0].kwargs["params"]["page"] == 1
    assert session.get.call_args_list[1].kwargs["params"]["page"] == 2


def test_list_all_pages_rejects_excessive_reported_page_count() -> None:
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _make_response(
            {
                "page": 1,
                "per_page": 20,
                "pages": 101,
                "items": [{"id": "first-item"}],
            },
        ),
    ]

    with pytest.raises(RuntimeError, match="reports 101 pages; maximum is 100"):
        list_all_pages(session, "https://api.civo.com/v2/sshkeys")

    assert session.get.call_count == 1


def test_list_all_pages_stops_on_single_page() -> None:
    # Arrange: "pages": 1 means there is nothing more to fetch.
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _make_response(
            {
                "page": 1,
                "per_page": 20,
                "pages": 1,
                "items": [{"id": "only-one"}],
            },
        ),
    ]

    # Act
    results = list_all_pages(session, "https://api.civo.com/v2/sshkeys")

    # Assert
    assert results == [{"id": "only-one"}]
    assert session.get.call_count == 1


def test_get_json_array_returns_bare_array() -> None:
    # Arrange: several Civo endpoints (firewalls, networks, subnets, volumes,
    # DNS, load balancers) return a bare JSON array, not the paginated wrapper.
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [_make_response([{"id": "a"}, {"id": "b"}])]

    # Act
    results = get_json_array(session, "https://api.civo.com/v2/firewalls")

    # Assert
    assert results == [{"id": "a"}, {"id": "b"}]


def test_get_json_array_rejects_non_list_body() -> None:
    # A malformed but HTTP-200 response (e.g. `{}`) must not be silently
    # treated as an authoritative (empty) inventory, or a subsequent
    # cleanup would delete every previously-ingested resource of this type.
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [_make_response({})]

    with pytest.raises(ValueError, match="non-array response body"):
        get_json_array(session, "https://api.civo.com/v2/firewalls")


def test_list_all_pages_rejects_non_list_items() -> None:
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _make_response({"page": 1, "per_page": 20, "pages": 1, "items": {}}),
    ]

    with pytest.raises(ValueError, match="non-list `items`"):
        list_all_pages(session, "https://api.civo.com/v2/sshkeys")


def test_require_non_empty_rejects_empty_and_missing() -> None:
    assert require_non_empty("real-id", "id") == "real-id"
    with pytest.raises(ValueError, match="missing required non-empty id"):
        require_non_empty("", "id")
    with pytest.raises(ValueError, match="missing required non-empty id"):
        require_non_empty(None, "id")


_FULL_FEATURES = {
    "iaas": True,
    "kubernetes": True,
    "object_store": True,
    "loadbalancer": True,
    "gpu": True,
    "dbaas": True,
    "volume": True,
    "paas": True,
    "public_ip_node_pools": True,
}


def test_get_regions_returns_full_region_objects() -> None:
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _make_response(
            [
                {"code": "lon1", "name": "London 1", "features": _FULL_FEATURES},
                {
                    "code": "nyc1",
                    "name": "New York 1",
                    "features": {**_FULL_FEATURES, "iaas": False},
                },
            ],
        ),
    ]

    results = get_regions(session, "https://api.civo.com")

    assert results == [
        {"code": "lon1", "name": "London 1", "features": _FULL_FEATURES},
        {
            "code": "nyc1",
            "name": "New York 1",
            "features": {**_FULL_FEATURES, "iaas": False},
        },
    ]


def test_get_regions_raises_when_features_object_is_missing() -> None:
    # A missing `features` object can't be distinguished from every feature
    # being explicitly false, which would wrongly exclude a genuinely
    # supported region from every feature-gated module's fetch.
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [_make_response([{"code": "lon1", "name": "London 1"}])]

    with pytest.raises(ValueError, match="missing its `features` object"):
        get_regions(session, "https://api.civo.com")


def test_get_regions_tolerates_a_missing_feature_key() -> None:
    # Live-tested against a real Civo account: the real /v2/regions response
    # does not carry a fixed key set per region at all (one region omitted
    # `public_ip_node_pools` entirely; this module doesn't even read that
    # key). A missing key is what "not supported here" looks like on the
    # real API - it must not raise, only a wholly missing `features` object
    # or a non-bool value for a key this module actually reads should.
    session = mock.MagicMock(spec=requests.Session)
    incomplete_features = {k: v for k, v in _FULL_FEATURES.items() if k != "dbaas"}
    session.get.side_effect = [
        _make_response(
            [{"code": "lon1", "name": "London 1", "features": incomplete_features}],
        ),
    ]

    results = get_regions(session, "https://api.civo.com")

    assert results[0]["features"] == incomplete_features
    assert region_codes_for_feature(results, "dbaas") == []


def test_get_regions_raises_when_a_feature_value_is_not_boolean() -> None:
    # `{"dbaas": null}` passes the "key exists" check but would still be
    # treated as falsy by region_codes_for_feature, wrongly excluding a
    # region that may genuinely support dbaas.
    session = mock.MagicMock(spec=requests.Session)
    null_dbaas_features = {**_FULL_FEATURES, "dbaas": None}
    session.get.side_effect = [
        _make_response(
            [{"code": "lon1", "name": "London 1", "features": null_dbaas_features}],
        ),
    ]

    with pytest.raises(ValueError, match="non-boolean value"):
        get_regions(session, "https://api.civo.com")


def test_get_regions_raises_on_empty_response() -> None:
    # An empty region list must fail loudly, not silently make every regional
    # fan-out load nothing while cleanup() still deletes previously-ingested
    # regional resources.
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [_make_response([])]

    with pytest.raises(ValueError, match="no regions"):
        get_regions(session, "https://api.civo.com")


def test_get_regions_rejects_region_with_no_code() -> None:
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [_make_response([{"name": "London 1"}])]

    with pytest.raises(ValueError, match="missing required non-empty region code"):
        get_regions(session, "https://api.civo.com")


def test_region_codes_for_feature_filters_by_flag() -> None:
    regions = [
        {"code": "lon1", "features": {"kubernetes": True, "volume": False}},
        {"code": "nyc1", "features": {"kubernetes": False, "volume": True}},
    ]

    assert region_codes_for_feature(regions, "kubernetes") == ["lon1"]
    assert region_codes_for_feature(regions, "volume") == ["nyc1"]


def test_region_codes_for_feature_none_returns_every_region_unfiltered() -> None:
    # Firewalls/Networks/Subnets/IPs have no Features flag at all, so
    # feature=None must return every region regardless of its features map.
    regions = [
        {"code": "lon1", "features": {"kubernetes": True}},
        {"code": "nyc1", "features": {}},
    ]

    assert region_codes_for_feature(regions, None) == ["lon1", "nyc1"]


def test_region_codes_for_feature_empty_result_is_not_an_error() -> None:
    # A real feature with zero supporting regions is legitimate, not a failure.
    regions = [{"code": "lon1", "features": {"kubernetes": False}}]

    assert region_codes_for_feature(regions, "kubernetes") == []


def test_fan_out_paginated_across_regions_queries_every_region_and_dedups() -> None:
    # Arrange: instances is a real region-scoped, paginated endpoint. The
    # same instance id turns up in both regions' responses (e.g. an endpoint
    # that doesn't actually filter by region) - must not be duplicated.
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _make_response(
            {"page": 1, "per_page": 20, "pages": 1, "items": [{"id": "i-1"}]},
        ),
        _make_response(
            {
                "page": 1,
                "per_page": 20,
                "pages": 1,
                "items": [{"id": "i-1"}, {"id": "i-2"}],
            },
        ),
    ]

    results = fan_out_paginated_across_regions(
        session, "https://api.civo.com/v2/instances", ["lon1", "nyc1"]
    )

    assert [item["id"] for item in results] == ["i-1", "i-2"]
    assert session.get.call_count == 2
    assert session.get.call_args_list[0].kwargs["params"]["region"] == "lon1"
    assert session.get.call_args_list[1].kwargs["params"]["region"] == "nyc1"
    # Each item is tagged with the region it was fetched from - the only
    # copy of that information for resource types with no native region field.
    assert [item["region"] for item in results] == ["lon1", "nyc1"]


def test_fan_out_paginated_across_regions_prefers_items_own_region() -> None:
    # Instance responses already carry their own `region` field - that must
    # win over the query's region_code (e.g. an endpoint that ignores the
    # region filter and returns results from elsewhere).
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _make_response(
            {
                "page": 1,
                "per_page": 20,
                "pages": 1,
                "items": [{"id": "i-1", "region": "nyc1"}],
            },
        ),
    ]

    results = fan_out_paginated_across_regions(
        session, "https://api.civo.com/v2/instances", ["lon1"]
    )

    assert results[0]["region"] == "nyc1"


def test_fan_out_array_across_regions_queries_every_region_and_dedups() -> None:
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _make_response([{"id": "n-1"}]),
        _make_response([{"id": "n-1"}, {"id": "n-2"}]),
    ]

    results = fan_out_array_across_regions(
        session, "https://api.civo.com/v2/networks", ["lon1", "nyc1"]
    )

    assert [item["id"] for item in results] == ["n-1", "n-2"]
    assert session.get.call_args_list[0].kwargs["params"]["region"] == "lon1"
    assert session.get.call_args_list[1].kwargs["params"]["region"] == "nyc1"
    assert [item["region"] for item in results] == ["lon1", "nyc1"]
