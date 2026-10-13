import cartography.intel.snowflake.users
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.users import SNOWFLAKE_USERS


def test_transform_treats_a_null_user_type_as_human():
    # Arrange: Snowflake leaves `type` unset for users created without one, and a
    # real account showed exactly that for its human admin.
    users = [{"name": "LENNY", "type": None}]

    # Act
    humans, services = cartography.intel.snowflake.users.transform(
        users, {}, SNOWFLAKE_ACCOUNT_ID
    )

    # Assert
    assert [user["name"] for user in humans] == ["LENNY"]
    assert services == []


def test_transform_leaves_mfa_null_when_it_could_not_be_read():
    # Arrange: SHOW USERS was not permitted, so enrollment is unknown.
    # Act
    humans, _ = cartography.intel.snowflake.users.transform(
        SNOWFLAKE_USERS, {}, SNOWFLAKE_ACCOUNT_ID
    )

    # Assert: unknown must stay null. Reporting false would claim every user is
    # unprotected, which is worse than admitting ignorance.
    assert {user["has_mfa"] for user in humans} == {None}


def test_transform_does_not_carry_the_redacted_password():
    # Arrange: the API returns `password: "********"`, which is not information.
    # Act
    humans, _ = cartography.intel.snowflake.users.transform(
        SNOWFLAKE_USERS, {}, SNOWFLAKE_ACCOUNT_ID
    )

    # Assert
    assert all("password" not in user for user in humans)
