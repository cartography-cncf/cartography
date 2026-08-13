from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.huntress.memberships import get
from cartography.intel.huntress.memberships import transform
from tests.data.huntress.memberships import MEMBERSHIPS

TEST_ACCOUNT_ID = 1000
TEST_BASE_URI = "https://api.huntress.io"


def _http_error(status_code: int) -> requests.exceptions.HTTPError:
    response = MagicMock()
    response.status_code = status_code
    return requests.exceptions.HTTPError(response=response)


@patch(
    "cartography.intel.huntress.memberships.get_paginated_huntress_items",
    side_effect=_http_error(403),
)
def test_get_returns_none_when_not_authorized(mock_get_paginated) -> None:
    """None, not an empty list: the caller must skip its cleanup rather than wipe users."""
    assert get(MagicMock(), TEST_BASE_URI) is None


@patch(
    "cartography.intel.huntress.memberships.get_paginated_huntress_items",
    side_effect=_http_error(500),
)
def test_get_propagates_other_http_errors(mock_get_paginated) -> None:
    with pytest.raises(requests.exceptions.HTTPError):
        get(MagicMock(), TEST_BASE_URI)


def test_transform_folds_memberships_into_users_and_roles() -> None:
    users, roles = transform(MEMBERSHIPS, TEST_ACCOUNT_ID)

    users_by_id = {user["id"]: user for user in users}
    assert set(users_by_id) == {6001, 6002}
    # Homer holds an account-wide grant and an organization-scoped one.
    assert users_by_id[6001]["role_ids"] == ["1000/Admin", "2002/Security Engineer"]
    assert users_by_id[6001]["organization_ids"] == [2002]
    assert users_by_id[6002]["role_ids"] == ["2001/Read-only"]
    assert users_by_id[6002]["organization_ids"] == [2001]

    assert {
        (role["id"], role["name"], role["scope"], role["organization_id"])
        for role in roles
    } == {
        ("1000/Admin", "Admin", "account", None),
        ("2001/Read-only", "Read-only", "org", 2001),
        ("2002/Security Engineer", "Security Engineer", "org", 2002),
    }


def test_transform_dedupes_a_role_shared_by_two_users() -> None:
    memberships = [
        {
            "id": 1,
            "permissions": "Admin",
            "user": {"id": 1, "email": "lisa@example.com", "name": "Lisa"},
        },
        {
            "id": 2,
            "permissions": "Admin",
            "user": {"id": 2, "email": "bart@example.com", "name": "Bart"},
        },
    ]

    users, roles = transform(memberships, TEST_ACCOUNT_ID)

    assert len(roles) == 1
    assert {user["role_ids"][0] for user in users} == {"1000/Admin"}


def test_transform_skips_a_membership_without_a_user() -> None:
    memberships = [{"id": 1, "permissions": "Admin", "user": None}]

    users, roles = transform(memberships, TEST_ACCOUNT_ID)

    assert users == []
    assert roles == []


def test_transform_keeps_a_user_whose_membership_has_no_permission_label() -> None:
    memberships = [
        {"id": 1, "permissions": None, "user": {"id": 1, "email": "maggie@example.com"}}
    ]

    users, roles = transform(memberships, TEST_ACCOUNT_ID)

    assert users == [
        {
            "id": 1,
            "email": "maggie@example.com",
            "name": None,
            "role_ids": [],
            "organization_ids": [],
        }
    ]
    assert roles == []
