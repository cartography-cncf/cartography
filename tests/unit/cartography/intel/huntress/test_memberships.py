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
    assert users_by_id[6001]["role_ids"] == [
        "account/1000/Admin",
        "org/2002/Security Engineer",
    ]
    assert users_by_id[6001]["organization_ids"] == [2002]
    assert users_by_id[6002]["role_ids"] == ["org/2001/Read-only"]
    assert users_by_id[6002]["organization_ids"] == [2001]

    assert {
        (role["id"], role["name"], role["scope"], role["organization_id"])
        for role in roles
    } == {
        ("account/1000/Admin", "Admin", "account", None),
        ("org/2001/Read-only", "Read-only", "org", 2001),
        ("org/2002/Security Engineer", "Security Engineer", "org", 2002),
    }


def test_transform_dedupes_a_role_shared_by_two_users() -> None:
    memberships = [
        {
            "id": 1,
            "permissions": "Admin",
            "account": {"id": TEST_ACCOUNT_ID},
            "user": {"id": 1, "email": "lisa@example.com", "name": "Lisa"},
        },
        {
            "id": 2,
            "permissions": "Admin",
            "account": {"id": TEST_ACCOUNT_ID},
            "user": {"id": 2, "email": "bart@example.com", "name": "Bart"},
        },
    ]

    users, roles = transform(memberships, TEST_ACCOUNT_ID)

    assert len(roles) == 1
    assert {user["role_ids"][0] for user in users} == {"account/1000/Admin"}


def test_transform_rejects_a_membership_without_a_user() -> None:
    """Skipping it would omit the user from the load while cleanup still deleted it."""
    memberships = [{"id": 1, "permissions": "Admin", "user": None}]

    with pytest.raises(ValueError, match="no user object"):
        transform(memberships, TEST_ACCOUNT_ID)


@pytest.mark.parametrize("bad_id", [None, "", "6001", 0.5, True])
def test_transform_rejects_an_unusable_user_id(bad_id):
    """A blank or non-integer id would collapse every malformed user onto one node."""
    memberships = [
        {
            "id": 1,
            "permissions": "Admin",
            "user": {"id": bad_id, "email": "lisa@example.com"},
        }
    ]

    with pytest.raises(ValueError, match="id is not an integer"):
        transform(memberships, TEST_ACCOUNT_ID)


def test_transform_keeps_a_user_whose_membership_has_no_permission_label() -> None:
    memberships = [
        {
            "id": 1,
            "permissions": None,
            "account": {"id": TEST_ACCOUNT_ID},
            "user": {"id": 1, "email": "maggie@example.com"},
        }
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


def test_transform_keeps_colliding_account_and_organization_ids_apart() -> None:
    """Account and organization ids come from separate sequences and can collide.

    Without the scope type in the role id, an account-wide `Admin` and an `Admin` scoped
    to the organization that happens to share the account's number would merge into one
    role, and each holder would be handed the other one's scope.
    """
    colliding_id = TEST_ACCOUNT_ID
    memberships = [
        {
            "id": 1,
            "permissions": "Admin",
            "account": {"id": colliding_id},
            "user": {"id": 1, "email": "lisa@example.com"},
        },
        {
            "id": 2,
            "permissions": "Admin",
            "organization": {"id": colliding_id},
            "user": {"id": 2, "email": "bart@example.com"},
        },
    ]

    users, roles = transform(memberships, TEST_ACCOUNT_ID)

    assert {(role["id"], role["scope"], role["organization_id"]) for role in roles} == {
        (f"account/{colliding_id}/Admin", "account", None),
        (f"org/{colliding_id}/Admin", "org", colliding_id),
    }
    users_by_id = {user["id"]: user for user in users}
    assert users_by_id[1]["role_ids"] == [f"account/{colliding_id}/Admin"]
    assert users_by_id[1]["organization_ids"] == []
    assert users_by_id[2]["role_ids"] == [f"org/{colliding_id}/Admin"]
    assert users_by_id[2]["organization_ids"] == [colliding_id]


def test_transform_rejects_an_organization_object_without_a_usable_id() -> None:
    """Regression: this used to silently widen an org grant into an account-wide role.

    Inferring "account-scoped" from a missing organization id made the graph report more
    access than the user actually holds.
    """
    memberships = [
        {
            "id": 1,
            "permissions": "Admin",
            "organization": {"name": "Springfield Elementary"},
            "user": {"id": 6001, "email": "homer@springfield.example.com"},
        }
    ]

    with pytest.raises(KeyError):
        transform(memberships, TEST_ACCOUNT_ID)


def test_transform_rejects_a_membership_with_no_scope_object() -> None:
    memberships = [
        {
            "id": 1,
            "permissions": "Admin",
            "user": {"id": 6001, "email": "homer@springfield.example.com"},
        }
    ]

    with pytest.raises(ValueError, match="neither an account nor an organization"):
        transform(memberships, TEST_ACCOUNT_ID)


def test_transform_rejects_a_membership_scoped_to_both() -> None:
    """The API documents a membership as carrying one scope object or the other."""
    memberships = [
        {
            "id": 1,
            "permissions": "Admin",
            "account": {"id": TEST_ACCOUNT_ID},
            "organization": {"id": 2001},
            "user": {"id": 6001, "email": "homer@springfield.example.com"},
        }
    ]

    with pytest.raises(ValueError, match="both an account and an organization"):
        transform(memberships, TEST_ACCOUNT_ID)


def test_transform_rejects_a_membership_from_another_account() -> None:
    """A membership for a different tenant has no business in this account's graph."""
    memberships = [
        {
            "id": 1,
            "permissions": "Admin",
            "account": {"id": TEST_ACCOUNT_ID + 1},
            "user": {"id": 6001, "email": "homer@springfield.example.com"},
        }
    ]

    with pytest.raises(ValueError, match="not the account being synced"):
        transform(memberships, TEST_ACCOUNT_ID)


@pytest.mark.parametrize("malformed", [2001, "Springfield Elementary", [], 0, False])
def test_transform_rejects_a_malformed_organization_alongside_an_account(malformed):
    """Regression: a non-object `organization` used to fall through to the account branch.

    That silently widened an organization grant into an account-wide role, which is the
    same over-reporting of access the scope validation exists to prevent.
    """
    memberships = [
        {
            "id": 1,
            "permissions": "Admin",
            "account": {"id": TEST_ACCOUNT_ID},
            "organization": malformed,
            "user": {"id": 6001, "email": "homer@springfield.example.com"},
        }
    ]

    with pytest.raises(ValueError, match="organization scope is not an object"):
        transform(memberships, TEST_ACCOUNT_ID)


@pytest.mark.parametrize("malformed", [1000, "Springfield Nuclear", []])
def test_transform_rejects_a_malformed_account_alongside_an_organization(malformed):
    """The mirror case: a garbage `account` field is not silently tolerated either."""
    memberships = [
        {
            "id": 1,
            "permissions": "Admin",
            "account": malformed,
            "organization": {"id": 2001},
            "user": {"id": 6001, "email": "homer@springfield.example.com"},
        }
    ]

    with pytest.raises(ValueError, match="account scope is not an object"):
        transform(memberships, TEST_ACCOUNT_ID)
