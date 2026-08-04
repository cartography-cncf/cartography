from datetime import datetime

from cartography.intel.miradore.users import transform
from tests.data.miradore.users import USERS

TEST_SITE_NAME = "simpsoncorp"


def test_transform_flattens_users() -> None:
    users = transform(USERS, TEST_SITE_NAME)

    marge = next(user for user in users if user["miradore_id"] == 2001)
    assert marge["email"] == "marge.simpson@simpson.corp"
    assert marge["name"] == "Simpson Marge"
    assert marge["firstname"] == "Marge"
    assert marge["lastname"] == "Simpson"
    assert marge["phone_number"] == "+358 50 1234 567"
    assert marge["source"] == "AD"
    assert marge["created"] == datetime(2024, 1, 5, 9, 0, 0)


def test_transform_derives_retired_from_the_status() -> None:
    users = transform(USERS, TEST_SITE_NAME)

    assert (
        next(user for user in users if user["miradore_id"] == 2001)["retired"] is False
    )
    assert (
        next(user for user in users if user["miradore_id"] == 2002)["retired"] is True
    )


def test_transform_leaves_retired_unset_without_a_status() -> None:
    (user,) = transform([{"ID": "2003", "Email": "bart@simpson.corp"}], TEST_SITE_NAME)

    assert user["retired"] is None
