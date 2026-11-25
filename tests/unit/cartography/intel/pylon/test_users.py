import pytest

from cartography.intel.pylon.users import transform


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ({"role_ids": ["b", "a"], "roles": [{"id": "c"}]}, ["a", "b"]),
        ({"roles": [{"id": "b"}, {"id": "a"}]}, ["a", "b"]),
        ({"role_ids": None, "roles": None, "role_id": "a"}, ["a"]),
        ({"role_ids": [], "roles": [{"id": "c"}]}, []),
        ({"roles": [], "role_id": "a"}, []),
        ({"role_id": ""}, []),
        ({}, []),
    ],
)
def test_transform_roles(fields, expected):
    # Arrange
    user = {"id": "user", "email": "user@example.com", **fields}

    # Act
    users, service_accounts = transform([user])

    # Assert
    assert users[0]["role_ids"] == expected
    assert service_accounts == []


@pytest.mark.parametrize("fields", [{}, {"email": ""}])
def test_transform_service_account(fields):
    # Arrange
    bot = {"id": "bot", "role_id": "admin", **fields}

    # Act
    users, service_accounts = transform([bot])

    # Assert
    assert users == []
    assert service_accounts[0]["id"] == "bot"
    assert service_accounts[0]["role_ids"] == ["admin"]
