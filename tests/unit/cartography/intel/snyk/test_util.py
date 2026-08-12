from unittest.mock import Mock

import pytest

from cartography.intel.snyk.util import _with_version
from cartography.intel.snyk.util import list_jsonapi_resources
from cartography.intel.snyk.util import relationship_id
from tests.data.snyk.data import ORG_COLLECTION_PAGE_1
from tests.data.snyk.data import ORG_COLLECTION_PAGE_2


class _Response:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        return None

    def json(self):
        return self.body


def test_list_jsonapi_resources_follows_next_link():
    session = Mock()
    session.get.side_effect = [
        _Response(ORG_COLLECTION_PAGE_1),
        _Response(ORG_COLLECTION_PAGE_2),
    ]

    result = list_jsonapi_resources(
        session, "https://api.snyk.io/rest/orgs/example/targets"
    )

    assert [item["id"] for item in result] == ["one", "two"]
    assert session.get.call_args_list[0].kwargs["params"]["version"] == "2024-10-15"
    assert session.get.call_args_list[1].args[0] == (
        "https://api.snyk.io/rest/orgs/example/targets?starting_after=cursor-1"
        "&version=2024-10-15"
    )
    assert session.get.call_args_list[1].kwargs["params"] is None


def test_list_jsonapi_resources_rejects_non_list_data():
    session = Mock()
    session.get.return_value = _Response({"data": {"id": "not-a-list"}})

    with pytest.raises(ValueError, match="expected list data"):
        list_jsonapi_resources(session, "https://api.snyk.io/rest/orgs/example/targets")


def test_list_jsonapi_resources_rejects_malformed_links():
    session = Mock()
    session.get.return_value = _Response({"data": [], "links": []})

    with pytest.raises(ValueError, match="malformed links"):
        list_jsonapi_resources(session, "https://api.snyk.io/rest/orgs/example/targets")


def test_list_jsonapi_resources_resolves_path_relative_next_link():
    session = Mock()
    session.get.side_effect = [
        _Response(
            {
                "data": [
                    {
                        "id": "one",
                        "type": "target",
                        "attributes": {"display_name": "one"},
                    }
                ],
                "links": {"next": "next-page?starting_after=cursor-1"},
            }
        ),
        _Response({"data": [], "links": {}}),
    ]

    list_jsonapi_resources(session, "https://api.snyk.io/rest/orgs/example/targets")

    assert session.get.call_args_list[1].args[0] == (
        "https://api.snyk.io/rest/orgs/example/next-page"
        "?starting_after=cursor-1&version=2024-10-15"
    )


def test_relationship_id_ignores_to_many_relationship_data():
    resource = {
        "id": "one",
        "relationships": {
            "projects": {
                "data": [
                    {"id": "project-one", "type": "project"},
                    {"id": "project-two", "type": "project"},
                ]
            }
        },
    }

    assert relationship_id(resource, "projects") is None


def test_with_version_only_treats_version_key_as_api_version():
    result = _with_version("https://api.snyk.io/rest/orgs/example?api_version=old")

    assert result == (
        "https://api.snyk.io/rest/orgs/example?api_version=old&version=2024-10-15"
    )
