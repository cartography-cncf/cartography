from typing import Dict
from typing import List

from cartography.intel.okta.groups import transform_okta_group
from cartography.intel.okta.groups import transform_okta_group_member_list
from tests.data.okta.groups import create_test_group
from tests.data.okta.groups import GROUP_MEMBERS_SAMPLE_DATA


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
