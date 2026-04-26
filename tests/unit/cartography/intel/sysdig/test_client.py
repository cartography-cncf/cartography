from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.sysdig.client import schema_has_entity
from cartography.intel.sysdig.client import SysdigClient


def test_query_paginates_until_short_page() -> None:
    client = SysdigClient("https://api.us1.sysdig.com", "token", page_size=2)
    first = Mock(status_code=200)
    first.json.return_value = {"data": [{"id": "1"}, {"id": "2"}]}
    second = Mock(status_code=200)
    second.json.return_value = {"data": [{"id": "3"}]}

    with patch.object(client.session, "request", side_effect=[first, second]) as req:
        assert client.query("MATCH n RETURN n") == [
            {"id": "1"},
            {"id": "2"},
            {"id": "3"},
        ]

    assert req.call_args_list[0].kwargs["json"]["query"].endswith("LIMIT 2 OFFSET 0")
    assert req.call_args_list[1].kwargs["json"]["query"].endswith("LIMIT 2 OFFSET 2")


def test_query_retries_retryable_status() -> None:
    client = SysdigClient("https://api.us1.sysdig.com", "token", page_size=2)
    retry = Mock(status_code=429)
    retry.raise_for_status.side_effect = requests.HTTPError("rate limited")
    ok = Mock(status_code=200)
    ok.json.return_value = {"data": []}

    with (
        patch("cartography.intel.sysdig.client.time.sleep"),
        patch.object(client.session, "request", side_effect=[retry, ok]) as req,
    ):
        assert client.query("MATCH n RETURN n") == []

    assert req.call_count == 2


def test_query_fails_fast_on_auth_status() -> None:
    client = SysdigClient("https://api.us1.sysdig.com", "token", page_size=2)
    forbidden = Mock(status_code=403)
    forbidden.raise_for_status.side_effect = requests.HTTPError("forbidden")

    with patch.object(client.session, "request", return_value=forbidden):
        with pytest.raises(requests.HTTPError):
            client.query("MATCH n RETURN n")


def test_schema_has_entity_walks_nested_schema() -> None:
    schema = {
        "entities": [
            {"name": "Vulnerability"},
            {"relationships": [{"target": {"name": "RuntimeEvent"}}]},
        ],
    }

    assert schema_has_entity(schema, "Vulnerability")
    assert schema_has_entity(schema, "RuntimeEvent")
    assert schema_has_entity({"KubeWorkload": {"fields": []}}, "KubeWorkload")
    assert not schema_has_entity(schema, "NotReal")


def test_get_schema_accepts_yaml_response() -> None:
    client = SysdigClient("https://api.us1.sysdig.com", "token")
    response = Mock(status_code=200)
    response.json.side_effect = ValueError("not json")
    response.text = "index:\n  - type: Entity\n    name: KubeWorkload\n"

    with patch.object(client.session, "request", return_value=response):
        schema = client.get_schema()

    assert schema_has_entity(schema, "KubeWorkload")
