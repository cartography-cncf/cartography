import json
from typing import Dict
from typing import List
from unittest import mock

import pytest

from cartography.intel.okta.groups import get_okta_group_members
from cartography.intel.okta.groups import transform_okta_group
from cartography.intel.okta.groups import transform_okta_group_member_list
from tests.data.okta.groups import create_test_group
from tests.data.okta.groups import GROUP_MEMBERS_SAMPLE_DATA


class _Response:
    def __init__(self, text: str) -> None:
        self.text = text
        self.headers: dict[str, str] = {}
        self.links: dict[str, dict[str, str]] = {}


def test_group_transform_with_all_values():
    group = create_test_group()

    result = transform_okta_group(group)

    expected = {
        "id": group.id,
        "name": group.profile.name,
        "description": group.profile.description,
        "sam_account_name": group.profile.samAccountName,
        "dn": group.profile.dn,
        "windows_domain_qualified_name": group.profile.windowsDomainQualifiedName,
        "external_id": group.profile.externalId,
    }

    assert result == expected


def test_group_transform_with_sam_account_none():
    group = create_test_group()
    group.profile.samAccountName = None

    result = transform_okta_group(group)

    expected = {
        "id": group.id,
        "name": group.profile.name,
        "description": group.profile.description,
        "sam_account_name": None,
        "dn": group.profile.dn,
        "windows_domain_qualified_name": group.profile.windowsDomainQualifiedName,
        "external_id": group.profile.externalId,
    }

    assert result == expected


def test_group_transform_with_windows_domain_none():
    group = create_test_group()
    group.profile.windowsDomainQualifiedName = None

    result = transform_okta_group(group)

    expected = {
        "id": group.id,
        "name": group.profile.name,
        "description": group.profile.description,
        "sam_account_name": group.profile.samAccountName,
        "dn": group.profile.dn,
        "windows_domain_qualified_name": None,
        "external_id": group.profile.externalId,
    }

    assert result == expected


def test_group_transform_with_external_id_none():
    group = create_test_group()
    group.profile.externalId = None

    result = transform_okta_group(group)

    expected = {
        "id": group.id,
        "name": group.profile.name,
        "description": group.profile.description,
        "sam_account_name": group.profile.samAccountName,
        "dn": group.profile.dn,
        "windows_domain_qualified_name": group.profile.windowsDomainQualifiedName,
        "external_id": None,
    }

    assert result == expected


def test_group_member_list_transform():
    """
    Simple test to see if `last_name` and `id` are present.
    """
    transformed_results: List[Dict] = transform_okta_group_member_list(
        GROUP_MEMBERS_SAMPLE_DATA,
    )
    last_names = [(r["last_name"], r["id"]) for r in transformed_results]

    assert len(last_names) == 3
    assert ("Clarkson", "OKTA_USER_ID_1") in last_names
    assert ("Hammond", "OKTA_USER_ID_3") in last_names
    assert ("May", "OKTA_USER_ID_2") in last_names


@mock.patch("cartography.intel.okta.groups.time.sleep", return_value=None)
def test_get_okta_group_members_retries_non_json_sdk_error(
    mock_sleep: mock.MagicMock,
) -> None:
    api_client = mock.MagicMock()
    response = _Response(json.dumps(GROUP_MEMBERS_SAMPLE_DATA))
    api_client.get_path.side_effect = [
        json.JSONDecodeError("Expecting value", "", 0),
        response,
    ]

    result = get_okta_group_members(api_client, "group-001")

    assert result == GROUP_MEMBERS_SAMPLE_DATA
    assert api_client.get_path.call_count == 2
    mock_sleep.assert_called_once_with(1)


@mock.patch("cartography.intel.okta.groups.time.sleep", return_value=None)
def test_get_okta_group_members_raises_after_non_json_sdk_retries(
    mock_sleep: mock.MagicMock,
) -> None:
    api_client = mock.MagicMock()
    api_client.get_path.side_effect = json.JSONDecodeError("Expecting value", "", 0)

    with pytest.raises(json.JSONDecodeError):
        get_okta_group_members(api_client, "group-001")

    assert api_client.get_path.call_count == 3
    assert mock_sleep.call_count == 2


def test_get_okta_group_members_raises_on_malformed_next_link() -> None:
    api_client = mock.MagicMock()
    response = _Response(json.dumps(GROUP_MEMBERS_SAMPLE_DATA))
    response.links = {"next": {}}
    api_client.get_path.return_value = response

    with pytest.raises(ValueError, match="missing a next URL"):
        get_okta_group_members(api_client, "group-001")

    api_client.get_path.assert_called_once()
    api_client.get.assert_not_called()
